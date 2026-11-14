#!/usr/bin/env python3
"""Safe, dependency-free management of local Karabiner complex modifications.

Designed for macOS, but supports Linux/CI testing with explicit paths.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

PROJECT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT / "rules" / "manifest.json"
DEFAULT_CONFIG = Path.home() / ".config" / "karabiner" / "karabiner.json"
DEFAULT_ASSETS = Path.home() / ".config" / "karabiner" / "assets" / "complex_modifications"
DEFAULT_BACKUP = Path.home() / "Library" / "Application Support" / "Karabiner-Elements-Automation" / "backups"
PREFIX = "bfa-"
# Specific rule descriptions distributed during earlier iterations of this project.
# Only these exact descriptions are automatically replaced. Other rules remain untouched.
LEGACY_DESCRIPTIONS = {
    "Safari Only: Command+Backtick switches windows via Command+Shift+Backtick",
    "Safari only: Command+Backtick switches windows via Command+Shift+Backtick",
    "Safari only: Map Command+Backtick to Command+Shift+Backtick for window switching",
    "Safari only: Command+Backtick switches windows using Command+Shift+Backtick",
    "Safari: Command+Backtick switches windows",
}

class RuleError(Exception):
    pass


def read_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        raise RuleError(f"Could not read valid JSON from {path}: {exc}") from exc


def validate_rule(rule, source):
    if not isinstance(rule, dict) or not isinstance(rule.get("description"), str) or not rule["description"].strip():
        raise RuleError(f"{source}: rule must have a nonempty string 'description'")
    manipulators = rule.get("manipulators")
    if not isinstance(manipulators, list) or not manipulators:
        raise RuleError(f"{source}: 'manipulators' must be a nonempty list (no 'rules' wrapper here)")
    for i, m in enumerate(manipulators):
        if not isinstance(m, dict) or m.get("type") != "basic":
            raise RuleError(f"{source}: manipulator {i} must be a basic object")
        if not isinstance(m.get("from"), dict) or not isinstance(m.get("to"), list) or not m["to"]:
            raise RuleError(f"{source}: manipulator {i} must have from object and nonempty to list")
    return rule


def load_rules(rules_dir: Path):
    manifest = read_json(rules_dir / "manifest.json")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or not isinstance(manifest.get("rules"), list) or not manifest["rules"]:
        raise RuleError("rules/manifest.json requires schema_version 1 and nonempty rules list")
    result, ids, descriptions = [], set(), set()
    for item in manifest["rules"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("file"), str):
            raise RuleError("Invalid rule manifest entry")
        rid, name = item["id"], item["file"]
        if not rid or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in rid) or name != rid + ".json":
            raise RuleError(f"Invalid rule id/file mapping: {rid!r} / {name!r}")
        if rid in ids:
            raise RuleError(f"Duplicate rule ID: {rid}")
        ids.add(rid)
        rule = validate_rule(read_json(rules_dir / name), rules_dir / name)
        if rule["description"] in descriptions:
            raise RuleError(f"Duplicate rule description: {rule['description']}")
        descriptions.add(rule["description"])
        result.append((rid, rule))
    return result


def is_target_trigger(m):
    if not isinstance(m, dict):
        return False
    source = m.get("from")
    if not isinstance(source, dict) or source.get("key_code") != "grave_accent_and_tilde":
        return False
    mods = source.get("modifiers", {})
    if not isinstance(mods, dict) or sorted(mods.get("mandatory", [])) != ["command"]:
        return False
    conditions = m.get("conditions", [])
    if not isinstance(conditions, list):
        return False
    return any(isinstance(c, dict) and c.get("type") == "frontmost_application_if"
               and "^com\\.apple\\.Safari$" in c.get("bundle_identifiers", []) for c in conditions)


def conflicts(existing, incoming):
    return any(is_target_trigger(m) for m in existing.get("manipulators", []) if isinstance(m, dict)) and any(
        is_target_trigger(m) for m in incoming.get("manipulators", []))


def initial_config():
    # Matches the documented overall root/profile structure. Karabiner may enrich
    # optional fields on its first launch.
    return {"global": {"check_for_updates_on_startup": True, "show_in_menu_bar": True},
            "profiles": [{"name": "Default profile", "selected": True,
                          "simple_modifications": [], "fn_function_keys": [], "devices": [],
                          "virtual_hid_keyboard": {"keyboard_type_v2": "ansi"},
                          "complex_modifications": {"rules": []}}]}


def load_config(path):
    if path.is_symlink():
        raise RuleError(f"Refusing to overwrite symlinked config file: {path}. Karabiner requires a regular file.")
    doc = read_json(path) if path.exists() else initial_config()
    if not isinstance(doc, dict) or not isinstance(doc.get("profiles"), list) or not doc["profiles"]:
        raise RuleError(f"{path}: expected an object with nonempty profiles list")
    return doc


def choose_profile(doc, name):
    profiles = doc["profiles"]
    if name is not None:
        matches = [p for p in profiles if isinstance(p, dict) and p.get("name") == name]
        if len(matches) != 1:
            raise RuleError(f"Profile {name!r} not found uniquely; available: {[p.get('name') for p in profiles]}")
        return matches[0]
    selected = [p for p in profiles if isinstance(p, dict) and p.get("selected") is True]
    if len(selected) == 1:
        return selected[0]
    if len(profiles) == 1 and isinstance(profiles[0], dict):
        return profiles[0]
    raise RuleError("No unique selected Karabiner profile; pass --profile NAME")


def preset_doc(rule):
    return {"title": "Karabiner-Elements-Automation", "rules": [copy.deepcopy(rule)]}


def serialize(doc):
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def backup_existing(path, backup_dir):
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    dst = backup_dir / f"{path.name}.{date}.{uuid.uuid4().hex[:8]}.bak"
    shutil.copy2(path, dst)
    if hashlib.sha256(dst.read_bytes()).digest() != hashlib.sha256(path.read_bytes()).digest():
        dst.unlink(missing_ok=True)
        raise RuleError(f"Backup verification failed for {path}")
    os.chmod(dst, 0o600)
    return dst


def atomic_write(path, payload, backup_dir):
    if path.is_symlink():
        raise RuleError(f"Refusing to replace symlinked file: {path}")
    if path.exists() and path.read_bytes() == payload:
        return None, False
    oldmode = (path.stat().st_mode & 0o777) if path.exists() else 0o600
    oldbackup = backup_existing(path, backup_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmpname = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        os.fchmod(handle, oldmode)
        with os.fdopen(handle, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmpname, path)
    finally:
        if os.path.exists(tmpname):
            os.unlink(tmpname)
    return oldbackup, True


def lint_with_installed_karabiner(presets):
    """Use Karabiner's own parser when installed, before editing user settings."""
    cli = shutil.which("karabiner_cli")
    if not cli:
        candidate = Path("/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli")
        if candidate.is_file() and os.access(candidate, os.X_OK):
            cli = str(candidate)
    if not cli:
        print("Karabiner CLI not found; validated bundled JSON structure only")
        return
    with tempfile.TemporaryDirectory(prefix="karabiner-rule-validation-") as temporary:
        for index, (_, payload) in enumerate(presets):
            if payload is None:
                continue
            filename = Path(temporary) / f"rule-{index}.json"
            filename.write_bytes(payload)
            result = subprocess.run([cli, "--lint-complex-modifications", str(filename)],
                                    capture_output=True, text=True, check=False)
            if result.returncode != 0:
                message = (result.stdout + result.stderr).strip()
                raise RuleError(f"Installed Karabiner CLI rejected rule: {message}")
    print("Installed Karabiner CLI validated the generated predefined rules")


def run(args):
    rules = load_rules(args.rules_dir)
    if args.action == "validate":
        for rid, rule in rules:
            print(f"OK: {rid}: {len(rule['manipulators'])} manipulator(s)")
        return
    # Preserve custom rules and unrelated profiles byte-for-byte semantically.
    document = load_config(args.config)
    selected = choose_profile(document, args.profile)
    profile_name = selected.get("name", "(unnamed)")
    cm = selected.setdefault("complex_modifications", {})
    if not isinstance(cm, dict) or not isinstance(cm.setdefault("rules", []), list):
        raise RuleError("Selected profile has malformed complex_modifications.rules")
    active = cm["rules"]
    managed_descriptions = {r["description"] for _, r in rules} | LEGACY_DESCRIPTIONS
    own_old = [r for r in active if isinstance(r, dict) and r.get("description") in managed_descriptions]
    other = [r for r in active if not (isinstance(r, dict) and r.get("description") in managed_descriptions)]
    planned_presets = []
    if args.action in {"install", "status"}:
        for rid, desired in rules:
            for old in other[:]:
                if conflicts(old, desired):
                    if not args.replace_conflicts:
                        raise RuleError(f"Conflicting Safari Command+Backtick rule: {old.get('description')!r}. "
                                        "Disable it manually or rerun with --replace-conflicts to replace it.")
                    other.remove(old)
            path = args.assets_dir / (PREFIX + rid + ".json")
            planned_presets.append((path, serialize(preset_doc(desired))))
        new_rules = [copy.deepcopy(r) for _, r in rules] + other
    elif args.action == "remove":
        new_rules = other
        planned_presets = [(args.assets_dir / (PREFIX + rid + ".json"), None) for rid, _ in rules]
    else:
        raise RuleError(f"Unknown action: {args.action}")
    changed_rules = active != new_rules
    cm["rules"] = new_rules
    if args.action == "status":
        print(f"Profile: {profile_name}")
        print(f"Active managed rule(s): {len(own_old)}; desired rules: {len(rules)}")
        print("Configuration:", args.config)
        missing_presets = []
        for path, content in planned_presets:
            installed = path.is_file() and path.read_bytes() == content
            print(f"Preset {path.name}: {'installed' if installed else 'missing/outdated'}")
            if not installed:
                missing_presets.append(path)
        if changed_rules or missing_presets:
            print("Status: installation incomplete/outdated")
            raise RuleError("Installed configuration or imported presets differ from repository; run install.command again")
        print("Status: up to date")
        return
    if args.dry_run:
        print(f"DRY RUN: action={args.action} profile={profile_name} config_change={changed_rules}")
        for path, content in planned_presets:
            print(f"DRY RUN: {'remove' if content is None else 'write'} {path}")
        return
    if args.action == "install":
        lint_with_installed_karabiner(planned_presets)
    # Prevalidate all destinations so failures do not partially change known files.
    if changed_rules and args.config.parent.exists() and not os.access(args.config.parent, os.W_OK):
        raise RuleError(f"Cannot write configuration directory: {args.config.parent}")
    for path, content in planned_presets:
        if path.is_symlink():
            raise RuleError(f"Refusing symlinked preset: {path}")
    # Save newly activated configuration before installing optional UI presets.
    if changed_rules:
        backup, _ = atomic_write(args.config, serialize(document), args.backup_dir)
        print(f"Updated profile: {profile_name}")
        if backup:
            print(f"Configuration backup: {backup}")
    else:
        print(f"Active rules already up to date in profile: {profile_name}")
    for path, content in planned_presets:
        if content is None:
            if path.exists():
                backup = backup_existing(path, args.backup_dir)
                path.unlink()
                print(f"Removed preset: {path} (backup: {backup})")
        else:
            backup, written = atomic_write(path, content, args.backup_dir)
            if written:
                print(f"Installed predefined-rule file: {path}")
                if backup: print(f"Previous preset backup: {backup}")
    print("Complete. Karabiner should reload the configuration automatically.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "install", "status", "remove"))
    parser.add_argument("--profile", help="Exact Karabiner profile name; default: selected profile")
    parser.add_argument("--replace-conflicts", action="store_true", help="Explicitly replace rules using the same Safari shortcut")
    parser.add_argument("--dry-run", action="store_true", help="Show intended changes without writing files")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP)
    parser.add_argument("--rules-dir", type=Path, default=PROJECT / "rules")
    args = parser.parse_args(argv)
    try:
        run(args)
    except (RuleError, OSError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

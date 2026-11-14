"""Tests use isolated temporary directories; never touch personal Karabiner files."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "manage_rules.py"
spec = importlib.util.spec_from_file_location("manage_rules", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RuleManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "config" / "karabiner.json"
        self.assets = self.root / "assets" / "complex_modifications"
        self.backups = self.root / "backups"
        self.rules_dir = ROOT / "rules"

    def cli(self, action, *args):
        return subprocess.run([sys.executable, str(SCRIPT), action, "--config", str(self.config),
                               "--assets-dir", str(self.assets), "--backup-dir", str(self.backups),
                               "--rules-dir", str(self.rules_dir), *args], capture_output=True, text=True)

    def assert_success(self, p):
        self.assertEqual(p.returncode, 0, p.stderr)

    def save(self, x):
        self.config.parent.mkdir(parents=True, exist_ok=True)
        self.config.write_text(json.dumps(x), encoding="utf-8")

    def rule(self):
        return json.loads((self.rules_dir / "safari-command-backtick-switch-windows.json").read_text())

    def test_validate(self):
        self.assert_success(self.cli('validate'))

    def test_new_install_creates_active_and_importable_files(self):
        self.assert_success(self.cli('install'))
        doc = json.loads(self.config.read_text())
        rule = doc['profiles'][0]['complex_modifications']['rules'][0]
        self.assertEqual(rule, self.rule())
        preset = json.loads((self.assets/'bfa-safari-command-backtick-switch-windows.json').read_text())
        self.assertEqual(preset['rules'], [self.rule()])
        self.assertEqual(preset['title'], 'Karabiner-Elements-Automation')
        self.assert_success(self.cli('status'))

    def test_idempotent_without_second_backup_or_file_rewrite(self):
        self.assert_success(self.cli('install'))
        before = self.config.stat().st_mtime_ns
        self.assert_success(self.cli('install'))
        self.assertEqual(self.config.stat().st_mtime_ns, before)
        self.assertEqual(len(list(self.backups.glob('*'))) if self.backups.exists() else 0, 0)

    def test_preserves_unrelated_profiles_settings_and_rules(self):
        doc = mod.initial_config()
        other = {'description': 'Other shortcut', 'manipulators': [{'type':'basic','from':{'key_code':'a'},'to':[{'key_code':'b'}]}]}
        doc['profiles'][0]['complex_modifications']['rules'] = [other]
        doc['profiles'][0]['custom_setting'] = {'hello':'world'}
        second = copy.deepcopy(doc['profiles'][0]); second['name'] = 'Work'; second['selected'] = False
        doc['profiles'].append(second)
        self.save(doc)
        self.assert_success(self.cli('install'))
        updated = json.loads(self.config.read_text())
        self.assertEqual(updated['profiles'][1], second)
        self.assertEqual(updated['profiles'][0]['custom_setting'], {'hello':'world'})
        self.assertEqual(updated['profiles'][0]['complex_modifications']['rules'][1], other)
        self.assertEqual(len(list(self.backups.glob('karabiner.json.*.bak'))), 1)
        self.assertEqual(json.loads(next(self.backups.glob('karabiner.json.*.bak')).read_text()), doc)

    def test_profile_override(self):
        doc = mod.initial_config()
        p = copy.deepcopy(doc['profiles'][0]); p['name']='Teacher'; p['selected']=False
        doc['profiles'].append(p)
        self.save(doc)
        self.assert_success(self.cli('install','--profile','Teacher'))
        updated = json.loads(self.config.read_text())
        self.assertEqual(updated['profiles'][0]['complex_modifications']['rules'], [])
        self.assertEqual(len(updated['profiles'][1]['complex_modifications']['rules']), 1)

    def test_ambiguous_selected_profile_fails_without_modification(self):
        doc = mod.initial_config()
        p = copy.deepcopy(doc['profiles'][0]); p['name']='Teacher'; p['selected'] = True
        doc['profiles'].append(p)
        self.save(doc)
        old = self.config.read_bytes()
        result = self.cli('install')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(old,self.config.read_bytes())

    def test_dry_run_never_writes_files(self):
        self.assert_success(self.cli('install','--dry-run'))
        self.assertFalse(self.config.exists())
        self.assertFalse(self.assets.exists())
        self.assertFalse(self.backups.exists())

    def test_unknown_conflicting_shortcut_refused_then_explicitly_replaced(self):
        doc = mod.initial_config()
        existing = copy.deepcopy(self.rule()); existing['description']='A different user-defined Safari rule'
        existing['manipulators'][0]['to']=[{'key_code':'f11'}]
        doc['profiles'][0]['complex_modifications']['rules']=[existing]
        self.save(doc)
        before = self.config.read_bytes()
        fail=self.cli('install')
        self.assertNotEqual(fail.returncode,0)
        self.assertIn('Conflicting',fail.stderr)
        self.assertEqual(before,self.config.read_bytes())
        self.assert_success(self.cli('install','--replace-conflicts'))
        updated = json.loads(self.config.read_text())
        self.assertEqual(updated['profiles'][0]['complex_modifications']['rules'],[self.rule()])

    def test_recognized_legacy_rule_replaced(self):
        doc=mod.initial_config()
        old=copy.deepcopy(self.rule());old['description']='Safari: Command+Backtick switches windows'
        doc['profiles'][0]['complex_modifications']['rules']=[old]
        self.save(doc)
        self.assert_success(self.cli('install'))
        self.assertEqual(json.loads(self.config.read_text())['profiles'][0]['complex_modifications']['rules'],[self.rule()])

    def test_uninstall_removes_only_managed_rules(self):
        doc = mod.initial_config()
        other = {'description':'Keep me','manipulators':[{'type':'basic','from':{'key_code':'a'},'to':[{'key_code':'b'}]}]}
        doc['profiles'][0]['complex_modifications']['rules']=[other]
        self.save(doc)
        self.assert_success(self.cli('install'))
        self.assert_success(self.cli('remove'))
        updated=json.loads(self.config.read_text())
        self.assertEqual(updated['profiles'][0]['complex_modifications']['rules'],[other])
        self.assertFalse((self.assets/'bfa-safari-command-backtick-switch-windows.json').exists())

    def test_symlinked_config_rejected(self):
        real=self.root/'real.json'; real.write_text(json.dumps(mod.initial_config()))
        self.config.parent.mkdir(parents=True,exist_ok=True)
        self.config.symlink_to(real)
        fail=self.cli('install')
        self.assertNotEqual(fail.returncode,0)
        self.assertIn('symlinked',fail.stderr)
        self.assertFalse(self.assets.exists())

    def test_invalid_config_rejected_without_clobber(self):
        self.config.parent.mkdir(parents=True,exist_ok=True)
        self.config.write_text('{bad json')
        fail=self.cli('install')
        self.assertNotEqual(fail.returncode,0)
        self.assertEqual(self.config.read_text(),'{bad json')

    def test_bad_rules_file_rejected_before_writing_config(self):
        import shutil
        copydir=self.root/'rules'
        shutil.copytree(self.rules_dir,copydir)
        (copydir/'safari-command-backtick-switch-windows.json').write_text('{"rules": []}')
        self.rules_dir=copydir
        fail=self.cli('install')
        self.assertNotEqual(fail.returncode,0)
        self.assertFalse(self.config.exists())

    def test_status_detects_missing_preset(self):
        self.assert_success(self.cli('install'))
        (self.assets/'bfa-safari-command-backtick-switch-windows.json').unlink()
        fail=self.cli('status')
        # A missing predefined file is incomplete, even though the shortcut is active.
        self.assertNotEqual(fail.returncode,0)
        self.assertIn('missing/outdated',fail.stdout)

    def test_installed_karabiner_linter_failure_prevents_changes(self):
        import os
        from unittest.mock import patch
        fakecli = self.root / "karabiner_cli"
        fakecli.write_text("#!/bin/sh\necho 'mock lint rejected file' >&2\nexit 1\n")
        fakecli.chmod(0o755)
        with patch.dict(os.environ, {"PATH": str(self.root) + os.pathsep + os.environ.get("PATH", "")}):
            result = self.cli('install')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('mock lint rejected file', result.stderr)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.assets.exists())

    def test_installed_karabiner_linter_success(self):
        import os
        from unittest.mock import patch
        fakecli = self.root / "karabiner_cli"
        fakecli.write_text("#!/bin/sh\n[ \"$1\" = '--lint-complex-modifications' ]\n")
        fakecli.chmod(0o755)
        with patch.dict(os.environ, {"PATH": str(self.root) + os.pathsep + os.environ.get("PATH", "")}):
            result = self.cli('install')
        self.assert_success(result)
        self.assertIn('validated the generated predefined rules', result.stdout)

    def test_dry_run_remove_does_not_change_install(self):
        self.assert_success(self.cli('install'))
        before=self.config.read_bytes()
        self.assert_success(self.cli('remove','--dry-run'))
        self.assertEqual(before,self.config.read_bytes())

if __name__=='__main__': unittest.main()

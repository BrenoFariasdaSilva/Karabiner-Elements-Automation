<div align="center">
  
# [Karabiner-Elements-Automation.](https://github.com/BrenoFariasdaSilva/Karabiner-Elements-Automation) <img src="https://github.com/BrenoFariasdaSilva/Karabiner-Elements-Automation/blob/d4173c3b2249a77b6b1a223b86e801ea2042eddc/.assets/Icons/GitHub%20Colored%20Icon.svg"  width="3%" height="3%">

</div>

<div align="center">
  
---

Install Karabiner-Elements on macOS, register custom complex modifications, and automatically enable them in the selected profile.
Independent project, not affiliated with Karabiner-Elements or Homebrew
  
---

</div>

<div align="center">

![GitHub Code Size in Bytes](https://img.shields.io/github/languages/code-size/BrenoFariasdaSilva/Karabiner-Elements-Automation)
![GitHub Commits](https://img.shields.io/github/commit-activity/t/BrenoFariasdaSilva/Karabiner-Elements-Automation/main)
![GitHub Last Commit](https://img.shields.io/github/last-commit/BrenoFariasdaSilva/Karabiner-Elements-Automation)
![GitHub Forks](https://img.shields.io/github/forks/BrenoFariasdaSilva/Karabiner-Elements-Automation)
![GitHub Language Count](https://img.shields.io/github/languages/count/BrenoFariasdaSilva/Karabiner-Elements-Automation)
![GitHub License](https://img.shields.io/github/license/BrenoFariasdaSilva/Karabiner-Elements-Automation)
![GitHub Stars](https://img.shields.io/github/stars/BrenoFariasdaSilva/Karabiner-Elements-Automation)
![GitHub Contributors](https://img.shields.io/github/contributors/BrenoFariasdaSilva/Karabiner-Elements-Automation)
![GitHub Created At](https://img.shields.io/github/created-at/BrenoFariasdaSilva/Karabiner-Elements-Automation)
![wakatime](https://wakatime.com/badge/github/BrenoFariasdaSilva/Karabiner-Elements-Automation.svg)

</div>

<div align="center">
  
![RepoBeats Statistics](https://repobeats.axiom.co/api/embed/8c8ffd6ec959368176d8a1903348d0adfb99760f.svg "Repobeats analytics image")

</div>

## Table of Contents
- [Karabiner-Elements-Automation. ](#karabiner-elements-automation-)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Requirements](#requirements)
  - [Setup](#setup)
    - [Clone the repository](#clone-the-repository)
  - [Installation:](#installation)
  - [Run Programing Language Code:](#run-programing-language-code)
    - [Dependencies](#dependencies)
    - [Dataset - Optional](#dataset---optional)
  - [Usage](#usage)
  - [Results - Optional](#results---optional)
  - [How to Cite?](#how-to-cite)
  - [Contributing](#contributing)
  - [Collaborators](#collaborators)
  - [License](#license)
    - [Apache License 2.0](#apache-license-20)

## Introduction

This repository provides a macOS bootstrapper and a dependency-free Python rule manager for [Karabiner-Elements](https://karabiner-elements.pqrs.org/). It turns **install Karabiner → import a custom JSON rule → enable the rule** into a repeatable operation without replacing unrelated user settings.

The supplied ZIP is a new, standalone repository ready for you to publish on GitHub; it does **not** create a remote repository or modify your existing projects.

## Requirements

- macOS (Apple Silicon or Intel), internet access for first-time software installation.
- Standard user account; install without `sudo`.
- Permission to approve software installation and Karabiner's macOS security dialogs.
- Python 3 for rule management (automatically installed if absent).

**Important macOS limitation:** Background Services, Accessibility, and Driver Extension approvals require user interaction in System Settings. No installer can legitimately bypass these protected permissions.

## Setup

### Clone the repository

1. Clone the repository with the following command:

   ```bash
   git clone https://github.com/BrenoFariasdaSilva/Karabiner-Elements-Automation.git
   cd Karabiner-Elements-Automation
   ```

## Installation:

* Programing Language:

  * Manually:
      ```bash
      # Programing Language:
      sudo apt install program-language -y
      ```

  * Using Makefile:
      ```bash
      make install
      ```

  * Using ShellScript:
      ```bash
      chmod +x install.sh
      sudo ./install.sh
      ```  

## Run Programing Language Code:

```bash
# Command here 
```

### Dependencies

1. Install the project dependencies with the following command:

   ```bash
   make dependencies
   ```

### Dataset - Optional

1. Download the dataset from [WEBSITE-HERE]() and place it in this project directory `(/Karabiner-Elements-Automation)` and run the following command:

   ```bash
   make dataset
   ```

## Usage

In order to run the project, run the following command:

```bash
make run
```

## Results - Optional

Discuss the results obtained in the project.

## How to Cite?

If you use the Repository-Name in your research, please cite it using the following BibTeX entry:

```
@misc{softwareRepository-Name:2024,
  title = {Repository-Name: Project-Description},
  author = {Breno Farias da Silva},
  year = {2024},
  howpublished = {https://github.com/BrenoFariasdaSilva/Repository-Name},
  note = {Accessed on September 11, 2024}
}
```

Additionally, a `main.bib` file is available in the root directory of this repository, in which contains the BibTeX entry for this project.

If you find this repository valuable, please don't forget to give it a ⭐ to show your support! Contributions are highly encouraged, whether by creating issues for feedback or submitting pull requests (PRs) to improve the project. For details on how to contribute, please refer to the [Contributing](#contributing) section below.

Thank you for your support and for recognizing the contribution of this tool to your work!

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**. If you have suggestions for improving the code, your insights will be highly welcome.
In order to contribute to this project, please follow the guidelines below or read the [CONTRIBUTING.md](CONTRIBUTING.md) file for more details on how to contribute to this project, as it contains information about the commit standards and the entire pull request process.
Please follow these guidelines to make your contributions smooth and effective:

1. **Set Up Your Environment**: Ensure you've followed the setup instructions in the [Setup](#setup) section to prepare your development environment.

2. **Make Your Changes**:
   - **Create a Branch**: `git checkout -b feature/YourFeatureName`
   - **Implement Your Changes**: Make sure to test your changes thoroughly.
   - **Commit Your Changes**: Use clear commit messages, for example:
     - For new features: `git commit -m "FEAT: Add some AmazingFeature"`
     - For bug fixes: `git commit -m "FIX: Resolve Issue #123"`
     - For documentation: `git commit -m "DOCS: Update README with new instructions"`
     - For refactorings: `git commit -m "REFACTOR: Enhance component for better aspect"`
     - For snapshots: `git commit -m "SNAPSHOT: Temporary commit to save the current state for later reference"`
   - See more about crafting commit messages in the [CONTRIBUTING.md](CONTRIBUTING.md) file.

3. **Submit Your Contribution**:
   - **Push Your Changes**: `git push origin feature/YourFeatureName`
   - **Open a Pull Request (PR)**: Navigate to the repository on GitHub and open a PR with a detailed description of your changes.

4. **Stay Engaged**: Respond to any feedback from the project maintainers and make necessary adjustments to your PR.

5. **Celebrate**: Once your PR is merged, celebrate your contribution to the project!

## Collaborators

We thank the following people who contributed to this project:

<table>
  <tr>
    <td align="center">
      <a href="#" title="defina o titulo do link">
        <img src="https://github.com/BrenoFariasdaSilva.png" width="100px;" alt="My Profile Picture"/><br>
        <sub>
          <b>Breno Farias da Silva</b>
        </sub>
      </a>
    </td>
  </tr>
</table>

## License

### Apache License 2.0

This project is licensed under the [Apache License 2.0](LICENSE). This license permits use, modification, distribution, and sublicense of the code for both private and commercial purposes, provided that the original copyright notice and a disclaimer of warranty are included in all copies or substantial portions of the software. It also requires a clear attribution back to the original author(s) of the repository. For more details, see the [LICENSE](LICENSE) file in this repository.

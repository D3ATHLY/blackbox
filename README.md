# BlackBox

<p align="center">
  <a href="https://github.com/D3ATHLY/blackbox/releases/latest"><img src="https://img.shields.io/github/v/release/D3ATHLY/blackbox?style=for-the-badge&label=Latest%20Release&labelColor=0b0b0d&color=2a2a2f" alt="Latest release" width="390" height="56"></a>
  <a href="https://github.com/D3ATHLY/blackbox/releases"><img src="https://img.shields.io/github/downloads/D3ATHLY/blackbox/total?style=for-the-badge&label=downloads&labelColor=0b0b0d&color=2a2a2f" alt="Total downloads" width="302" height="56"></a>
  <a href="https://github.com/D3ATHLY/blackbox/stargazers"><img src="https://img.shields.io/github/stars/D3ATHLY/blackbox?style=for-the-badge&label=stars&labelColor=0b0b0d&color=2a2a2f" alt="Stars" width="224" height="56"></a></p>

<p align="center">
  <a href="https://www.buymeacoffee.com/BlackBoxPS" target="_blank" title="buymeacoffee">
    <img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExM2FoZmV2cW12NmxueGR6M25yOG50bHN2MndjbzJzamtmNDV2aWZ2YyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/7kZE0z52Sd9zSESzDA/giphy.gif" alt="buymeacoffee-animated-badge">
  </a>
</p>





BlackBox is a homebrew storefront and download manager developed for PS5 consoles.

## Latest Release & Installation

* **Latest Release:** [Download Here](https://github.com/D3ATHLY/blackbox/releases/latest)
* **Installation Instructions:** *Please refer directly to the [latest release page](https://github.com/D3ATHLY/blackbox/releases/latest) for the official step-by-step `.elf` / `.ffpkg` installation procedures provided by the developer.*

---

### 🎮 Step-by-Step Installation

* **Delete the Old File:** Manually delete the old **PPSA01453.ffpkg** file located inside the `/data/homebrew` directory.
* **Uninstall Old Version:** Completely delete/uninstall the **older version of BlackBox** from your console.
* **Download the Latest Version:** Get the updated file from the official [BlackBox Latest Release Page] https://github.com/D3ATHLY/blackbox/releases/latest
* **Transfer the New File:** Copy the newly downloaded **PPSA01453.ffpkg** file into the `/data/homebrew` folder.
* **Trigger the Installation:** Use **shadowmount** to trigger and install the newly placed `.ffpkg` file.
* **Reboot if Needed:** If you still encounter warnings or errors, restart your console and try again.

> ⚠️ **CRITICAL WARNING:** **NEVER use Payload Manager** during this process! The `blackbox.elf` file is embedded inside `PPSA01453.ffpkg` and updates automatically. Do NOT load `blackbox.elf` manually via payload manager.

---


## Disclaimer and Terms of Use

* This project is provided "as is".
* This project does not host any game files, copyrighted content, or third-party software. The `catalog/` directory only contains game metadata (titles, cover image links, format information); the `updates/` directory solely contains the application's own update stream files.
* All file downloading and installation operations are at the user's own risk. This tool is intended exclusively for content to which the user has legal access rights.
* This project is not a commercial service. No fees are charged, and no subscription is required.
* No warranties are provided. The developers, contributors, and associated parties of the project assume no liability for any software or hardware issues, data loss, legal consequences, or any other damages.
* This project does not guarantee the security, legality, or copyright compliance of files accessed from third-party sources (e.g., Archive.org, Vikingfile); this responsibility belongs entirely to the user.
* By using this tool, the user agrees to comply with all applicable laws, terms of service, and copyright regulations.
* This project is not designed for unauthorized access, piracy, or illegal activities and must not be used for such purposes.
* Anyone using this project is deemed to have accepted the terms above.

## Content and Liability Limits

| Location | Content | Responsibility |
| :--- | :--- | :--- |
| `updates/payloads.json` | Application's own update information (version, SHA-256) | Developer |
| `updates/tv-app.json` | TV application update information | Developer |
| `catalog/` directory | Game metadata (title, cover, format, size) | Compiled from third-party sources |
| Release assets | `blackbox.elf`, `PPSA01453.ffpkg` (own compilation) | Developer |

* **Note:** Users should not download and directly use any files from this repository; the application operates via its own update mechanism. 
* Game files (FFPFSC, PKG, etc.) are never published or hosted in this repository.

## What This Project Is Not

* It is not a game store or content distributor.
* It is not designed for jailbreaking, unauthorized access, or any illegal operations.
* It does not automatically distribute third-party files; the user manually adds content.

## License

This project is licensed under the **GPL-3.0 or later** license. For detailed license information, see the `LICENSE` file. 

For third-party components and their licenses, see `catalog/README.md` and the respective `THIRD-PARTY-NOTICES` files (shipped with the release assets).

## Contact

For technical questions or bug reports, please use the [Issues](../../issues) section.

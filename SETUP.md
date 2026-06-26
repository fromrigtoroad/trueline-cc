# iRacing Telemetry Overlay

## For your followers

1. Go to the **Releases** page on GitHub
2. Download `iRacingOverlay-Setup.exe`
3. Double-click it → Next → Next → Finish
4. Launch **iRacing Telemetry Overlay** from the Start Menu

---

## For you (publishing a new release)

You only need to do the first-time setup once, then every release is just a git tag.

### First-time setup

1. Install [Git for Windows](https://git-scm.com)
2. Create a free account at [github.com](https://github.com)
3. Create a new repository (e.g. `iracing-overlay`), keep it public
4. Open Git Bash in this folder and run:
   ```
   git init
   git remote add origin https://github.com/YOUR_USERNAME/iracing-overlay.git
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```
5. Add your `assets/icon.ico` file (see assets/README.txt)

### Publishing a release

Whenever you want to ship a new version:

```
git add .
git commit -m "describe what changed"
git tag v1.0.0
git push && git push --tags
```

GitHub will automatically:
- Build the .exe on a Windows cloud machine
- Wrap it in an installer
- Publish it under **Releases** with a download link

Change `v1.0.0` to `v1.1.0`, `v1.2.0` etc. for future releases.

---

## How to save a reference .ibt in iRacing

In iRacing go to **Options → Graphics** and enable **Telemetry**.
After a session, `.ibt` files are saved to:
`Documents\iRacing\telemetry\`

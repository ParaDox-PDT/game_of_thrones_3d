# GitHub upload and Netlify production verification

- Repository: https://github.com/ParaDox-PDT/game_of_thrones_3d
- Branch: `main`
- Application commit: `fd90f13d714b73f23e5c08f771c055d92ce837ee` (`first commit`)
- Production: https://game-of-thrones-3d.netlify.app
- Immutable deploy: https://6ad06f542dc60af976502df7--game-of-thrones-3d.netlify.app
- Netlify site ID: `45d536a5-6323-4b19-bd0f-becd5a667d4e`
- Deploy ID: `6ad06f542dc60af976502df7`
- Published: 2026-10-15 06:15:34 UTC

The deployed website uses the expanded pass-04 winter environment. It loads the 32.4 MB LOD1 for interactive viewing and provides both LOD1 and the 91.7 MB master as downloads. Camera positions, terrain collision, walking spawn, landmark views, atmospheric fog, sunlight and embedded torch lighting match the expanded environment.

The production Next.js static export built successfully. Headless Chrome verified the live model rendering, landmark buttons, atmosphere controls, pointer-lock walking through the outer gate, collision at the inner defensive wall, two current model downloads and a 390 px mobile viewport with no horizontal overflow. No page errors or failed requests were recorded. HTTP checks confirmed the homepage, current manifest and both full-size GLB files respond successfully.

See `local/` and `production/` for browser screenshots and detailed test reports, `http-validation.json` for public asset checks, and `netlify-deploy.json` for deployment URLs. Frame-rate readings in these reports are observations on this workstation, not performance guarantees.

Deployment uses a CLI upload of the tested `out/` directory. The repository is pushed to GitHub; Git continuous deployment has not been connected. Future source changes require a new build and deploy:

```powershell
npm ci
npm run build
netlify link --id 45d536a5-6323-4b19-bd0f-becd5a667d4e
netlify deploy --dir out --prod --no-build
```

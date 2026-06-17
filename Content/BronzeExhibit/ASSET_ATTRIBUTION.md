# Bronze Exhibit Asset Attribution

## Current Placeholder Assets

The Bronze Exhibit integration currently uses only project-local level actors and Unreal Engine basic-shape placeholder meshes:

| Usage | Asset or Source | Status |
|---|---|---|
| Artifact stage | `/Engine/BasicShapes/Cylinder.Cylinder` | Unreal Engine placeholder |
| Artifact placeholder | `/Engine/BasicShapes/Sphere.Sphere` | Unreal Engine placeholder |
| Floor and backdrop | `/Engine/BasicShapes/Cube.Cube` | Unreal Engine placeholder |
| Lighting and atmosphere | Unreal Engine actor classes plus existing actors in `ScreenBasedPrefabDemo` | Project-local setup |

No external artwork, scans, fonts, textures, audio, or third-party marketplace assets are currently included by this integration.

## Future Asset Admission Rules

External exhibit assets may be admitted only when all of the following are true:

- Visual assets are released under CC0 or an equivalently unrestricted public-domain dedication.
- Fonts are released under the SIL Open Font License (OFL).
- The source page, creator, license name, license URL, direct download URL, and retrieval date are recorded before import.
- The downloaded archive or source file includes a license file when one is provided by the publisher.
- Assets with unclear authorship, unclear license scope, non-commercial restrictions, attribution-only terms, share-alike terms, or marketplace redistribution restrictions are not admitted.
- Modified assets retain a note describing the project-side changes.

## Source Record Template

Copy this section for every future external asset:

```text
Asset name:
Project path:
Purpose:
Creator:
Source page URL:
Direct download URL:
License:
License URL:
Retrieved on (YYYY-MM-DD):
Original filename:
Modifications:
Local license file path:
Reviewed by:
Review date (YYYY-MM-DD):
```

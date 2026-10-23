Installed 2026-10-24 for YanYue Unity production.
Source: https://github.com/tipoLi5890/unity-dev-skills
Commit: 1d41f203000f9dd5b442495ce683c12c036b5b27
Path: skills/unity-2d-pixel-perfect
License: MIT, original text in LICENSE.
Scope: Unity URP pixel-art import, camera and motion checks.
Sibling skills mentioned in the original document are not installed by this operation.
Derived from the pinned upstream resources; local corrections are documented below.
No downloaded C# helper executed during installation or this correction.
User's production authorization covers this project's import/camera changes; do not ask repeated approval solely from the skill's generic Report-then-wait guidance.

Local corrections, 2026-10-24:
- SKILL.md, all three reference documents and CameraSetupURP.cs comments correct the public URP rendering-extension API, requiresUpscalePass semantics, Grid/PPU assumptions and unsupported minimum-version claim.
- Verified only by source inspection against Unity 6000.3.27f1 and resolved com.unity.render-pipelines.universal 17.3.0. No claim of an earlier/later compatibility range, helper execution or custom renderer-feature runtime validation.
- Source evidence: Runtime/2D/Rendergraph/Renderer2DRendergraph.cs (standard passes' RecordRenderGraph and upscale OR condition); Runtime/ScriptableRenderer.cs (standard features' AddRenderPasses); Runtime/2D/RendererFeatures/ScriptableRenderPass2D.cs (internal/conditional types); Runtime/2D/PixelPerfectCamera.cs and PixelPerfectCameraInternal.cs (requiresUpscaling).
- Upstream MIT copyright and LICENSE are preserved unchanged. Local corrections do not claim to be an upstream release.
- Independent source review also corrected the API table's blanket post-processing prohibition and CropFrame aspect/bar claims: URP 17.3 retains a low-resolution post-processing path and StretchFill uses a centered aspect-preserving fit.
- quick_validate checks skill packaging/frontmatter, not technical correctness or rendered output. Independent review and repository synchronization are reported separately by the executing agents.

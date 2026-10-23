# Motion and the upscale — Cinemachine, UI text, post-processing, physics stutter

> Part of the `unity-2d-pixel-perfect` skill. `SKILL.md` §6, §7 and §8 state the rules; this file
> holds the limits, the ranked alternatives and the routing behind them. Confirm each fix in a
> windowed run: the upscale symptoms need a canvas and a volume in the scene, and micro-stutter
> needs play mode with a moving rigidbody — a headless Editor shows none of them.

## 1. Cinemachine writes orthographic size too

The camera's orthographic size is owned by the pixel-perfect component. Cinemachine writes it
every frame as well, and the loser is whichever ran first: jitter, plus framing that pops between
shots. So the **`CinemachinePixelPerfect` extension** must be on every camera rig, on the rig's
own GameObject — the Add Extension dropdown puts it there; on a child or a parent it never
registers with the rig. It calls the component's `CorrectCinemachineOrthoSize(float)` and hands
back the nearest pixel-perfect size, which is what makes the two agree.

Follow, dead zones, confiners, blends and the component names for each Cinemachine major:
`unity-camera` → `reference/pixel-perfect-follow.md`.

## 2. `UpscaleRenderTexture` versus UI text and post-processing

One cause, two symptoms: the scene is rendered small and then scaled up, and anything that runs
after that scale-up — or gets caught inside it — is working at the wrong resolution.

**Post-processing.** Inspect the actual upscale/post-processing order and the effect's sampling
in the resolved URP version. An enlarged buffer filtered later can lose crisp edges; trying
`gridSnapping = PixelSnapping` avoids that low-resolution buffer when its aesthetic is unnecessary.
A custom pass is a separate implementation task, not a guaranteed sharpening fix.

In the source-checked **Unity 6000.3.27f1 / URP 17.3.0**, use the public
`ScriptableRendererFeature` and `ScriptableRenderPass` APIs. Set a public `RenderPassEvent`
(for example `AfterRenderingPostProcessing` when the intended order requires it), enqueue the
pass through the feature, and override `RecordRenderGraph` for Render Graph rendering. Record
raster work through `RenderGraph.AddRasterRenderPass` and declare its resource dependencies.

Evidence in the resolved URP package:

- `Runtime/2D/Rendergraph/Renderer2DRendergraph.cs`, `RecordCustomRenderGraphPasses`: iterates
  ordinary `ScriptableRenderPass` instances and calls `RecordRenderGraph`.
- `Runtime/ScriptableRenderer.cs`, `AddRenderPasses`: invokes ordinary renderer features.
- `Runtime/2D/RendererFeatures/ScriptableRenderPass2D.cs`: `RenderPassEvent2D` is internal;
  `ScriptableRenderPass2D` is internal and conditionally compiled. They are not extension base
  types for game assemblies. No `ScriptableRendererFeature2D` exists in this checked package.

Thus a standard renderer feature is **not categorically ignored** by the 2D renderer. Its
renderer assignment, injection point, required resources and pass culling still need validation.
Do not copy internal types or extrapolate this source check to every Unity 6/URP release. A
windowed Frame Debugger/Render Graph check and rendered result are still required for a new pass;
no custom feature was executed during this skill correction. `OnRenderImage`/`Graphics.Blit`
is not a URP Render Graph injection mechanism. If available, `unity-render-urp` →
`reference/render-graph-review.md` supplies an additional review workflow.

**UI text.** A Screen Space – Camera canvas renders into the low-resolution buffer and is scaled
up with the scene, so text softens while the art stays crisp. Confirm the behaviour on your Unity
version in a windowed run before committing a canvas architecture to it. In reliability order:

1. Set the canvas to **Screen Space – Overlay**. It bypasses the camera entirely and draws at
   native resolution. This is the route that holds.
2. A separate UI camera with no pixel camera component on it, canvas in Screen Space – Camera.
3. Raise the font material's sharpness — on the material's Inspector, **Font Material → Debug
   Settings → Sharpness**, moved towards `1`. It addresses SDF threshold calibration at low
   reference resolutions and nothing about the buffer, so it is a partial mitigation: the text
   is still being scaled up with the scene.

Canvas render modes and scaler behaviour are `unity-ui-ugui`; CJK and SDF font atlases are
`unity-game-ui` → `reference/text-and-cjk.md`.

## 3. Micro-stutter is physics, not rendering

A sprite driven by `Rigidbody2D` stutters while everything else in the scene is smooth. Physics
advances on a fixed timestep and rendering does not, so the sprite's position is stale on frames
with no physics step and jumps on frames with one — then snapping quantises the result differently
each frame, which makes a sub-pixel error visible.

- `Rigidbody2D.interpolation = RigidbodyInterpolation2D.Interpolate` on every physics-driven
  sprite. This is the fix; the rest is tightening.
- Match the fixed timestep to the frame rate you actually run at (`Time.fixedDeltaTime = 1f / 60f`
  for 60 fps), so a step and a frame stay in step.
- Camera follow belongs in `LateUpdate`, after everything that moved this frame. In
  `FixedUpdate` the camera samples positions the renderer will not use.

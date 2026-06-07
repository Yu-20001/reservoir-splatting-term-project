# Reservoir Splatting Extension API Map

## Scene Mutation

- Candidate files include
  - `Source/Falcor/Scene/Scene.h:734`
  - `Source/Falcor/Scene/Scene.cpp:4259`
  - `Source/Falcor/Scene/SceneBuilder.h:617`
  - `Source/Falcor/Scene/SceneBuilder.cpp:1030`
- Relevant APIs include
  - `void Scene::updateNodeTransform(uint32_t nodeID, const float4x4& transform)`
    updates an existing runtime scene node and calls
    `AnimationController::setNodeEdited(nodeID)`.
  - `SceneBuilder::addNode()`, `SceneBuilder::addMeshInstance()`, and
    `SceneBuilder::addAnimation()` are construction-time APIs available while
    importing a scene.
  - The Python scene builder exposes `addNode`, `addMeshInstance`,
    `addAnimation`, and `Animation::addKeyframe()`.
- Observation: `Scene` exposes runtime transform editing, but it does not expose
  an equivalent direct runtime mesh-instance insertion API.

## Acceleration Structure Updates

- Candidate files include
  - `Source/Falcor/Scene/Animation/AnimationController.h:101`
  - `Source/Falcor/Scene/Scene.cpp:1882`
  - `Source/Falcor/Scene/Scene.cpp:1913`
  - `Source/Falcor/Scene/Scene.cpp:3939`
  - `Source/Falcor/Scene/Scene.cpp:4040`
- Relevant update flags or methods include
  - `AnimationController::setNodeEdited()` marks externally edited nodes.
  - `Scene::update()` converts changed node matrices into
    `SceneGraphChanged | GeometryMoved`.
  - `GeometryMoved` invalidates the TLAS cache and refreshes geometry instance
    descriptors.
  - `Scene::bindShaderDataForRaytracing()` rebuilds a missing invalidated TLAS.
  - Existing animation scenes may use TLAS refit through
    `RtAccelerationStructureBuildFlags::AllowUpdate` and `PerformUpdate`.
- Observation: existing-node transform updates already flow through the Falcor
  TLAS synchronization path. A Phase 2 prototype should verify this behavior
  with a moving preloaded mesh before adding broader UI.

## ReservoirSplatting UI

- Candidate files include
  - `Source/RenderPasses/ReservoirSplatting/ReservoirSplatting.cpp:378`
  - `Source/RenderPasses/ReservoirSplatting/ReservoirSplatting.cpp:399`
  - `Source/RenderPasses/ReservoirSplatting/ReservoirSplatting.cpp:511`
  - `Source/RenderPasses/ReservoirSplatting/ReservoirSplatting.cpp:1420`
- Existing UI entry point
  - `ReservoirSplatting::renderUI(Gui::Widgets& widget)` owns the pass UI and is
    the narrowest insertion point for a small dynamic-object prototype panel.
  - `ReservoirSplatting::execute()` is the corresponding per-frame update point.
- Constraint
  - `ReservoirSplatting::setScene()` warns that custom primitives are not
    supported, so the V1 object library should use triangle meshes.

## Lowest-Risk V1 Extension

- Selected route: preload a small fixed triangle-mesh object library as scene
  nodes, hide inactive nodes outside the room, and implement spawn/reset plus
  simplified gravity by updating one selected node transform each frame.
- Reason: runtime node transforms already trigger Falcor's scene graph and TLAS
  update path. Runtime mesh insertion is not exposed as a similarly direct
  `Scene` API and would expand the implementation surface unnecessarily.

## Phase 2 Plan Inputs

- Object library representation: pre-authored triangle-mesh nodes with
  non-delta materials in a project-owned `.pyscene`.
- Transform update entry point is
  `Scene::updateNodeTransform(uint32_t nodeID, const float4x4& transform)`.
- TLAS update behavior: edited nodes are marked through
  `AnimationController::setNodeEdited()`, surfaced as `GeometryMoved`, and cause
  TLAS invalidation and regeneration on the ray-tracing bind path.
- UI insertion point: add a compact dynamic-object group under
  `ReservoirSplatting::renderUI()` and update gravity state from
  `ReservoirSplatting::execute()`.

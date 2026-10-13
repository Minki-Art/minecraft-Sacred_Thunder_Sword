Sacred Thunder Sword
[English](README.md) | [中文](README_zh.md)

# 圣雷剑 Sacred Thunder Sword

A Fabric mod（Minecraft **1.21/1.21.1/1.21.11**）：Right-click to charge; release to fire a **lightning bolt**. 
The lightning automatically homes in on enemies near the crosshair and ignites the target on hit.

![mod icon](src/main/resources/assets/lightning_sword/icon.png)

---

Preview：
![Preview1](picture/2026-10-12_21.45.02.png)
![Preview2](picture/2026-10-12_21.45.12.png)
![Preview3](picture/2026-10-12_21.41.36.png)
![Preview4](picture/2026-10-12_21.41.53.png)

## Gameplay

| | |
|---|---|
| **Hold Right-Click** | Start charging, sword sparks with electricity, sword switches to "Aiming" mode |
| **Charge less than 0.4s** | Nothing happens if released |
| **Fully charged 2s** | Maximum range reaches 24 blocks (proportionally less if not fully charged, minimum 8 blocks) |
| **Release** | The tip of the sword shoots out a lightning bolt |
| **Hit damage** | **10 true damage** (ignores armor and armor enchantments, but resistance boosts still apply) |
| **Hit effect** | **Ignites target for 5s** (like fire aspect). The ignite is applied **before** dealing damage, so pigs, cows, and sheep killed by it drop **cooked meat** |
| **Auto-Tracking** | As long as the target is within **1.5 blocks** horizontally in the crosshair line, it will auto-lock, won't lock through walls |
| **Blocked by blocks** | Lightning stops at the block surface |
| **Each shot** | Consumes 1 durability, 10 ticks cooldown |
| **Melee** | **15 base damage / 1.8 attack speed**, with the same **sweeping edge** effect as a regular sword |

Melee values are generated using vanilla's own SwordItem.createAttributeModifiers(ToolMaterials.NETHERITE, 10, -2.2F)
(total damage = player base 1 + 10 + Netherite material 4 = 15, attack speed = 4.0 − 2.2 = 1.8),
so the attribute modifier IDs, enchantment checks, and attribute tooltips are all consistent with vanilla swords, and Sharpness and other enchantments work normally.

Auto-tracking's 1.5 blocks is lateral distance, not an angle, so it feels the same at all ranges.
If it's too sticky or too loose, just change the single value LightningBeam.AIM_ASSIST_RADIUS.

The lightning itself is not made of particles; instead, it copies vanilla LightningEntityRenderer's geometry generation code (8-segment random walk + 4-layer ribbon + the same RenderLayer.getLightning() lightning material), only changing the coordinate mapping from "vertically upward from the ground" to "along the flight direction". The shape is regenerated every frame, so it crackles and flickers instead of being a static texture.

First-person eye comfort handling: The part of the lightning less than 2.2 blocks from the camera is clipped (third-person is unaffected), and it does not use ParticleTypes.FLASH at all—that is vanilla's full-screen white flash particle, and spawning it in front of the player is very harsh.

## Crafting

1. **Thunder Crystal**：only in **End City loot chests**，With an**8.8% chance per chest** 。
   It is a **crystal (item).**
2. **Smithing Table**: `Netherite Sword` + `Netherite Upgrade Smithing Template` + `Thunder Crystal` → **Sacred Thunder Sword**.

## Installation

1. Install Fabric Loader (≥ 0.15.11) for Minecraft 1.21/1.21.1/1.21.11
2. Put Fabric API into mods/
3. Put lightning-sword-1.0.0.jar into mods/

## Code Structure

```
src/main/java/com/dsh/lightningsword/
├── LightningSwordMod.java          Entry: registers items, network packets, injects End City loot table
├── ModItems.java                   Sacred Thunder Sword (vanilla attribute approach) + Thunder Crystal
├── LightningSwordItem.java         ★ Charge/release firing, melee, idle sparks, repair, tooltip
├── LightningBeam.java              ★ Server side: raycast, 1.5-block auto-tracking, 10 true damage, ignite before damage
├── network/LightningBeamPayload.java  S2C custom packet (start/end/seed)
└── client/
    ├── LightningSwordClient.java   Client entry: receive packets, render events, tick, Sodium keep-alive hook
    ├── BeamRenderer.java           ★ Copies vanilla lightning geometry, draws along flight direction + near-end clipping (**do not change the implementation**)
    ├── ClientBeams.java            Lightning currently displayed (5 ticks, shape changes every frame)
    └── SwordSprites.java           Keeps the sword/crystal 8-frame animations running under Sodium (no-op without Sodium)

tools/
├── sword_source.png                Your sword concept art
├── crystal_source.png              Your crystal concept art
├── build_sword_texture.py          Sword concept art → 8-frame animated sword texture (overlay flowing arcs + outline glow)
├── build_crystal_texture.py        Crystal concept art → remove background + crop → 8-frame animated crystal texture
├── make_textures.py                Icon + pixel-style fallback textures (automatically skips corresponding textures when concept art exists)
├── gen_sword_model.py              ★ Extrudes sword texture silhouette into a 3D model (front/back/thickness)
├── preview_sword_model.py          Model structure self-check + preview render (no need to enter the game)
├── PoseSim.java / PoseSolve.java   Pose math simulator and solver (legacy, **currently no longer in tools/**)
├── resourcepack-template/          Resource pack template (textures only, no compilation needed)
└── patch_zipfs.py                  jdk.zipfs patch for DSH sandbox
```

## License

MIT

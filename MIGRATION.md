# 迁移到更高版本的完整清单

下面每一条都是**用 Yarn 映射实际核对过**的（1.21.1+build.3 对比 1.21.11+build.6），不是我凭印象写的。
核对脚本在 `D:\mcmod\tools\yarn_diff.py`，换任何 Yarn 版本都能重跑。

---

## 第 0 步：先决定目标版本（这一步最关键）

| 目标 | Yarn 映射 | Fabric API | 代价 |
|---|---|---|---|
| **1.21.11** | `1.21.11+build.6` ✅ 有 | `0.141.6+1.21.11` | 中：只改 API，包名基本不变 |
| **26.1 / 26.2 / 26.3** | ❌ **完全没有** | `0.162.0+26.3` | 大：**必须换 Mojang 官方映射，全代码改名** |

Minecraft 从 26.1 开始改成按年编号，而 **Yarn 只发布到 1.21.11**（我查了 yarn 的 maven 元数据，
3412 个版本里没有一个 `26.` 开头）。

所以：

- **想省事 → 迁到 1.21.11**。包名几乎不变，只需要改下面列的 API。
- **想跟最新 → 迁到 26.x**，但要接受：所有 Minecraft 符号改名
  （`World`→`Level`、`PlayerEntity`→`Player`、`Item.Settings`→`Item.Properties`、
  `Vec3d`→`Vec3`、`net.minecraft.util.Identifier`→`net.minecraft.resources.ResourceLocation` …），
  也就是说每一行 Java 都要动。做法是用 Loom 的 `officialMojangMappings()` 替代 Yarn。

> 本文档以 **1.21.11** 为主线；26.x 的差别见文末。

---

## 第 1 步：改配置

### `gradle.properties`

```properties
minecraft_version=1.21.11
yarn_mappings=1.21.11+build.6
loader_version=0.19.5          # 用 https://meta.fabricmc.net/v2/versions/loader 查最新
loom_version=<新的 loom>       # 1.9.2 太旧，必须换；见下
fabric_version=0.141.6+1.21.11 # 用 modrinth API 查对应版本
```

查版本的两个接口（浏览器直接打开就行）：

- Yarn：`https://meta.fabricmc.net/v2/versions/yarn/<游戏版本>`
- Fabric API：`https://api.modrinth.com/v2/project/fabric-api/version?game_versions=["<游戏版本>"]&loaders=["fabric"]`
- Loom：`https://maven.fabricmc.net/net/fabricmc/fabric-loom/maven-metadata.xml`

### `build.gradle`

`loom` 插件版本要跟着换（新版游戏需要新版 Loom）。26.x 还要换映射方式：

```groovy
dependencies {
    minecraft "com.mojang:minecraft:${project.minecraft_version}"
    // 26.x 没有 Yarn，用官方映射：
    // mappings loom.officialMojangMappings()
    mappings "net.fabricmc:yarn:${project.yarn_mappings}:v2"
    ...
}
```

### `fabric.mod.json`

```json
"depends": {
  "fabricloader": ">=0.16.0",
  "minecraft": ">=1.21.11 <1.22",
  "java": ">=21",
  "fabric-api": "*"
}
```

顺便：**accessWidener 可以删掉了**，见下面第 3 节（新版本不再需要它）。

---

## 第 2 步：Python 侧不用动

`tools/` 里的贴图生成器（`make_textures.py` / `build_sword_texture.py` /
`build_crystal_texture.py` / `gen_sword_model.py` / `preview_sword_model.py`）**和游戏版本无关**，一行都不用改。

> **2026-10 校正：** `gen_aim_models.py`、`PoseSim.java`、`PoseSolve.java` 这三个文件
> **当前并不存在**（`tools/` 里已经没有），下面提到它们的段落只作历史记录。

---

## 第 3 步：代码改动清单（1.21.1 → 1.21.11）

### 3.1 剑的创建方式整个换了

| 现在（1.21.1） | 1.21.11 |
|---|---|
| `class LightningSwordItem extends SwordItem` | `SwordItem` **类被删除** → 改成 `extends Item` |
| `new SwordItem(ToolMaterials.NETHERITE, settings)` | `ToolMaterials` **枚举被删除** → 现在是 `ToolMaterial` **record**，常量写成 `ToolMaterial.NETHERITE` |
| `SwordItem.createAttributeModifiers(material, 10, -2.2F)` | `ToolMaterial.NETHERITE.applySwordSettings(settings, 10, -2.2F)` |

新写法大致是：

```java
public static final Item LIGHTNING_SWORD = new LightningSwordItem(
        ToolMaterial.NETHERITE.applySwordSettings(
                new Item.Settings().maxCount(1).rarity(Rarity.EPIC).fireproof(), 10, -2.2F));
```

`applySwordSettings(settings, 基础伤害, 攻速)` 会一次性把攻击力/攻速/耐久/可附魔标签/横扫所需的组件
都设好 —— 所以**横扫效果仍然自动具备**，不用额外做什么。

`ToolMaterial` 在 1.21.11 是个 record，字段是
`repairItems / durability / speed / attackDamageBonus / enchantmentValue / incorrectBlocksForDrops`。

### 3.2 物品组件相关的 API 改名

| 现在 | 1.21.11 |
|---|---|
| `Item.Settings.attributeModifiers(...)` | **被删除** → `.component(DataComponentTypes.ATTRIBUTE_MODIFIERS, 组件)` |
| `Item.canRepair(stack, ingredient)` 覆写 | **方法被删除** → 改用 `.component(DataComponentTypes.REPAIRABLE, ...)` |

`DataComponentTypes` 里这些还在：`ATTRIBUTE_MODIFIERS`、`WEAPON`、`TOOL`、`REPAIRABLE`、
`ENCHANTABLE`、`MAX_DAMAGE`、`DAMAGE`、`ENCHANTMENT_GLINT_OVERRIDE`（附魔闪光那条不用改）。

### 3.3 `UseAction` 只是换了包

```
net/minecraft/util/UseAction   →   net/minecraft/item/consume/UseAction
```

类名没变，改 import 即可。`UseAction.BOW` 那套姿势逻辑不变。

### 3.4 ★ 模型谓词被整套删除 → 改用「物品模型定义」JSON

> **2026-10 校正（与实际文件逐行核对过）：** `lightning_sword.accesswidener` **确实已删除**
> （`fabric.mod.json` 里那行遗留声明也已移除），但 `ModelPredicateProviderRegistry` **还在**
> （见 `client/LightningSwordClient.java`），`lightning_sword.json` 也是
> 「`parent: minecraft:item/handheld` + `textures` + `overrides`」，不是「基模 + display + elements」。
> 目前 overrides 已由 8 条收敛为 1 条（阈值 0.5 → `lightning_sword_aim_5`），因为谓词只会返回 0.0 / 0.75。
> 迁移到 1.21.11 时只要注意 `elements` 的写法没变、`texture_size` 仍在，不用再搬 `items/*.json`。

| 现在 | 1.21.11 |
|---|---|
| `ModelPredicateProviderRegistry` | **删除**（已经删了） |
| `ClampedModelPredicateProvider` | **删除**（已经删了） |
| `models/item/xxx.json` 里的 `overrides` | **删除**（已经删了） |

替代品是 1.21.4 引入的**物品模型定义**：

- 新文件：`assets/<命名空间>/items/<物品id>.json`（注意是 `items/`，不是 `models/item/`）
- 里面用 `type: minecraft:range_dispatch` + `property: minecraft:using_item`
  这类**数据驱动**的属性来切模型
- 相关类（1.21.11 映射里能查到）：
  `client/render/item/model/RangeDispatchItemModel`、
  `client/render/item/property/bool/UsingItemProperty`

**对本 mod 反而是好事**：8 套瞄准姿势不用再写 Java 谓词、不用 accessWidener，
纯 JSON 就能表达「蓄力时切换到某个模型」。但**按 `P` 切换预设**这种运行时行为
要重新设计（物品模型定义是静态的，得换成 8 个不同物品？或者改用客户端渲染钩子）。

### 3.5 ★ 闪电渲染要重写

| 现在 | 1.21.11 |
|---|---|
| `RenderLayer.getLightning()` | **删除**（1.21.5 整个渲染管线被重写） |

新体系是 `com.mojang.blaze3d.pipeline.RenderPipeline`（+ `Builder`）、
`net.minecraft.client.gl.RenderPipelines`、`net.minecraft.client.render.RenderLayers`。

所以 `client/BeamRenderer.java` **需要重写**：要么用新 API 注册一个自己的
`RenderPipeline` + `RenderLayer`，要么退化成纯粒子实现（把 `LightningBeam` 里那层
兜底电火花粒子加浓就够看）。

**好消息**：几何生成那部分不受影响 ——
`LightningEntityRenderer` 和它的 `drawBranch`、以及 `VertexConsumer` 在 1.21.11 里**都还在**，
照搬原版闪电几何的代码可以原样保留。

### 3.6 核对过、**不用改**的部分

这些在 1.21.11 里依然存在且同名（脚本确认过）：

`LightningEntityRenderer` · `VertexConsumer` · `HeldItemRenderer` ·
`AttributeModifiersComponent` · `AttributeModifierSlot` · `DataComponentTypes` ·
`LootPool` · `ItemEntry` · `RandomChanceLootCondition` · `ConstantLootNumberProvider` ·
`RegistryKeys` · `ProjectileUtil` · `PlayerEntity` · `RaycastContext` · `CustomPayload` ·
`ParticleTypes` · `SoundEvents`

方法级：`getUseAction` · `getMaxUseTime` · `usageTick` · `onStoppedUsing` · `appendTooltip` ·
`inventoryTick` · `use` · `setOnFireFor` · `getRotationVec` · `indirectMagic` ·
`raycast` · `getOtherEntities` · `getBoundingBox` · `getEyePos` · `addParticle` ·
`setCurrentHand` · `isUsingItem` · `getItemUseTimeLeft` · `getActiveItem` ·
`spawnParticles` · `getDamageSources` · `getItemCooldownManager`

→ 也就是说 `LightningBeam.java`（追踪/真伤/点燃/音效）**基本可以原样保留**，
主要工作在渲染和物品注册那两块。

---

## 第 4 步：资源文件

| 项目 | 要不要改 |
|---|---|
| `assets/<ns>/textures/item/*.png` + `.mcmeta` | 不用改 |
| `assets/<ns>/models/item/*.json`（手持模型） | 保留，但 `overrides` 那套要搬到 `assets/<ns>/items/*.json` |
| `assets/<ns>/lang/*.json` | 不用改 |
| `data/<ns>/recipe/*.json` | 不用改（锻造台格式没变） |
| `data/<ns>/loot_table/*` | 不用改 |
| `data/minecraft/tags/item/swords.json` | 不用改 |
| `data/<ns>/advancement/*.json` | 格式大概率不用改，但**移植后必须看日志**确认加载成功（成就加载失败只报日志，编译不管） |
| `lightning_sword.accesswidener` | **已删除**（姿势切换移除后就不再需要） |

---

## 第 5 步：实际操作顺序

```bash
# 1) 复制一份工程，别在原目录上改
# 2) 改 gradle.properties + build.gradle + fabric.mod.json
# 3) 先让它跑起来，把新依赖拉全
pwsh -File .\build-lightning-sword.ps1
# 4) 看这个 mod 用到的符号在两版之间变了什么
python D:\mcmod\tools\yarn_diff.py 1.21.11+build.6
# 5) 逐个修编译错误（编译器会把清单直接列给你）
# 6) 细节拿不准时，反编译新版本看源码
pwsh -File .\build-lightning-sword.ps1 -Task genSources
#    源码在  .gradle/loom-cache/minecraftMaven/**/*-sources.jar
```

**建议的迁移顺序**（从易到难，每步都能先编译过再往下）：

1. 配置 + `fabric.mod.json` → 空工程能编译
2. `ModItems`（`ToolMaterial.applySwordSettings`、组件改名）
3. `LightningSwordItem`（`extends Item`、`UseAction` 换包、`canRepair` 换组件）
4. `LightningBeam`（大概率不用动）
5. 物品模型定义 JSON（姿势切换）
6. `BeamRenderer` 渲染重写（最难，放最后）

---

## 26.x 的额外差别

1. **没有 Yarn**，`build.gradle` 里换成 `loom.officialMojangMappings()`。
2. 然后所有 Minecraft 符号都要按 Mojang 名字改，例如：

   | Yarn | Mojang |
   |---|---|
   | `net.minecraft.util.Identifier` | `net.minecraft.resources.ResourceLocation` |
   | `net.minecraft.world.World` | `net.minecraft.world.level.Level` |
   | `net.minecraft.entity.player.PlayerEntity` | `net.minecraft.world.entity.player.Player` |
   | `net.minecraft.item.Item.Settings` | `net.minecraft.world.item.Item.Properties` |
   | `net.minecraft.util.math.Vec3d` | `net.minecraft.world.phys.Vec3` |
   | `net.minecraft.util.math.BlockPos` | `net.minecraft.core.BlockPos` |
   | `net.minecraft.registry.Registries` | `net.minecraft.core.registries.BuiltInRegistries` |
   | `getWorld()` | `level()` |
   | `isClient()` | `isClientSide()` |

   改法：改完映射直接编译，按报错一个个替换；**不要手工全局替换**，因为同名不同义的很多。
3. 26.x 属于跨了好几个大版本，除了上面那些，可能还有 1.21.11 之后新引入的改动；
   用 `gradle genSources` 拉源码逐个确认，比猜可靠。

---

## 一句话总结

- **省事路线**：迁 **1.21.11**，改 4 个类 + 一套物品模型 JSON，逻辑代码基本不动。
- **最新路线**：迁 **26.x**，额外要把 Mojang 映射的改名全做一遍。
- 无论哪条，**贴图生成脚本和数学工具都不用动**，`LightningBeam` 的玩法逻辑也基本不用动 ——
  主要成本在**物品注册方式**、**模型切换系统**、**自定义渲染**这三块。

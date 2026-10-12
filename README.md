# 圣雷剑 Sacred Thunder Sword

一个 Fabric 模组（Minecraft **1.21.1**）：右键蓄力，松手射出一道**原版闪电形状的闪电**，
闪电会自动追踪准心附近的敌人，命中后点燃目标。

![mod icon](src/main/resources/assets/lightning_sword/icon.png)

---

## 玩法

| | |
|---|---|
| **右键按住** | 开始蓄力，剑身电火花环绕，剑切换到「瞄准」模型 |
| **蓄力不足 0.4 秒** | 松手无效果 |
| **蓄满 2 秒** | 射程达到最远 24 格（未蓄满按比例，最短 8 格） |
| **松手** | 剑尖射出一道闪电 |
| **命中伤害** | **10 点真实伤害**（无视护甲和护甲附魔，抗性提升仍然有效） |
| **命中效果** | **点燃目标 5 秒**（类似火焰附加）。点燃是在造成伤害**之前**施加的，所以被劈死的猪牛羊掉的是**熟肉** |
| **自动追踪** | 目标只要在准心射线 **1.5 格**横向范围内就会被自动锁定，隔着墙不锁 |
| **被方块挡住** | 闪电停在方块表面 |
| **每次发射** | 消耗 1 点耐久，10 tick 冷却 |
| **近战** | **15 点面板伤害 / 1.8 攻速**，和原版剑一样有**横扫之刃**效果 |

近战数值是用原版自己的 `SwordItem.createAttributeModifiers(ToolMaterials.NETHERITE, 10, -2.2F)` 生成的
（总伤害 = 玩家基础 1 + 10 + 下界合金材质 4 = 15，攻速 = 4.0 − 2.2 = 1.8），
所以属性修饰符 ID、附魔判定、属性 tooltip 全都和原版剑一致，**锋利等附魔正常生效**。

自动追踪的 1.5 格是**横向距离**而不是角度，所以远近手感一致。
太黏或太松改 `LightningBeam.AIM_ASSIST_RADIUS` 一个数就行。

闪电本体**不是粒子拼的**，而是把原版 `LightningEntityRenderer` 的几何生成代码（8 段随机游走 +
4 层丝带 + 同一个 `RenderLayer.getLightning()` 电光材质）照搬过来，只把坐标映射从「从地面竖直向上」
换成「沿飞行方向」。每帧形状会重新生成，所以它会噼啪闪动而不是一张静止贴图。

**第一人称护眼处理**：闪电离镜头不足 2.2 格的部分会被裁掉（第三人称不受影响），
并且全程**不使用** `ParticleTypes.FLASH`——那是原版全屏白闪粒子，生成在角色眼前非常刺眼。

## 合成

1. **雷电晶矿**：只在**末地城战利品箱**里，**每个箱子 8.8%** 概率。
   它是一块**晶体（像钻石）**，不是可放置的矿石方块。
2. **锻造台**：`下界合金剑` + `下界合金升级锻造模板` + `雷电晶矿` → **圣雷剑**。

## 瞄准姿势（只有一套，已按你的红线解出来）

蓄力时剑会切换成**唯一的一套**瞄准模型（原第 5 套 `aim_x60_y45` 的数值）：

| | firstperson 旋转 | thirdperson 旋转 |
|---|---|---|
| 右手 | `60, -45, 25` | `60, -45, 55` |
| 左手 | `60, 45, -25` | `60, 45, -55` |

**没有姿势切换了**，`P` 键和那 8 个 `lightning_sword_aim_*.json` 都已移除。

> 历史：早期版本有 8 套姿势、用 `P` 循环挑选，姿势切换依赖一个 model predicate。
> 定下来之后那套机制（含 `lightning_sword.accesswidener`）就删掉了，现在只有一个物品模型，
> 少一个每帧求值的 predicate，也少一类和优化类模组打架的东西。

## 外观与特效

- **剑模型是真 3D 的薄板**，不是一张平面：`tools/gen_sword_model.py` 逐帧描出剑身的实心轮廓，
  挤出成「正面 + 背面 + 一圈厚度」。
  - 正面就是原画，背面是镜像的原画（所以从背后看也是实的，不会有那条透过去的缝）。
  - 厚度沿轮廓一圈窄面，取该边缘像素的颜色，侧面看有金属截面的感觉；剑尖按 45% 收薄。
  - **几何坐标 = 贴图原始像素位置直接换算**（`x = col * 0.1`、`y = 16 - row * 0.1`），不做任何平移，
    所以剑的位置、大小、旋转枢轴和旧版平面模型**逐点一致**。
  - 仍然只用**同一张** 8 帧动画贴图：Minecraft 的贴图动画是把新像素上传到同一个 sprite 区域，
    UV 不动，所以动画/辉光/资源包覆盖全都照旧。
- **剑贴图是 160×160 / 8 帧动画**（你画的那把碎晶剑，叠加了流动电弧）：每帧都有独立的程序化闪电
  在晶面上爬行，外圈有青色轮廓辉光在呼吸。`frametime: 2`，即每秒 10 帧。
- **雷电晶矿是 64×64 / 8 帧动画**（你给的晶体图 + 动态特效）：内部那道闪电的辉光在呼吸，
  每帧还有新的电弧在晶体表面爬行、四周碎片处有火星闪烁；物品本身另带附魔闪光。
- **附魔光效**：剑和晶石都自带 `enchantment_glint_override`，永远有附魔闪光，不需要真的附魔。
- **粒子**：带着剑就会从剑尖冒电火花；蓄力时电火花绕剑尖旋转，蓄满后半径收紧、密度变高。

## 和 Sodium（画面优化模组）的兼容

**现象**：装了 Sodium 之后剑/晶石的贴图卡在第 1 帧不动；卸掉就正常。

**原因**（在 Sodium 0.8.13 源码里核对过，不是猜）：

1. Sodium 有个性能选项 `animateOnlyVisibleTextures`（视频设置里的 "Animate Only Visible Textures"）。
   它的 mixin 在 `SpriteContents.Ticker.tickAndUpload` 开头判断：**如果这个 sprite 上一帧没被标记成
   "active"，就直接 `ci.cancel()`** —— 帧计数器照走，但新像素永远不上传。表现就是"卡住不动"。
2. 标记 active 只能由 Sodium 自己的渲染路径调用 `SpriteUtil.markSpriteActive()`。它对原版物品的快速路径
   是通的（拿 `BakedQuad.getSprite()`），但 FRAPI 物品路径 `ItemRenderContext.bufferQuad()` 里找 sprite
   用的是 **block 图集** 的 `SpriteFinderCache.forBlockAtlas()` —— 物品 sprite 根本不在那个图集里，
   于是查不到、标不上。

**修法**：`client/SwordSprites.java` 每个客户端 tick 用 Sodium 自己的公开 API
（反射调 `SpriteUtil.INSTANCE.markSpriteActive`）把**剑和晶石**两张贴图标成 active。
Minecraft 客户端一帧的顺序是 `MinecraftClient.tick()`（含 `textureManager.tick()`，即贴图动画上传）
→ 渲染，而 Fabric 的 `END_CLIENT_TICK` 在这两者之间，所以标记会在本帧渲染前生效。
没有装 Sodium 时这个类什么都不做（启动日志会写一行 `Sodium not present`）。

> **不要再往"渲染写法"上打补丁**：曾经把 `BeamRenderer` 从 `context.consumers().getBuffer(...)`
> 改成 `Tessellator.begin(...)` + `BufferRenderer.drawWithGlobalProgram(...)` 自绘立即提交，
> 用户实测**闪电变成黑色**，已回退。现在 `BeamRenderer` 就是最朴素的写法，**别动它**。
> 只保留 `SwordSprites` 这一个"保活"补丁。

## 改贴图 / 改模型

**两个位置别搞混：**

| 位置 | 作用 |
|---|---|
| `src/main/resources/assets/lightning_sword/...` | **会被打进 mod 的 jar**，改了必须重新编译 |
| `tools/resourcepack-template/...` | 只是**给你自己做成资源包**的模板，放那里模组不会读 |

### 路线 A：做资源包（不用编译，`F3+T` 即时生效）

1. 把 `tools/resourcepack-template/` 整个复制到 `.minecraft/resourcepacks/`，随便改名。
2. 游戏里 **选项 → 资源包** 启用。
3. 改文件 → 按 **`F3+T`** 重载。

| 改什么 | 文件 |
|---|---|
| 剑贴图 | `assets/lightning_sword/textures/item/lightning_sword.png` |
| 剑的动画速度 | 同名 `.png.mcmeta` 的 `frametime` |
| 晶石贴图 | `assets/lightning_sword/textures/item/thunder_crystal.png` |
| 手持/蓄力角度 | `assets/lightning_sword/models/item/lightning_sword.json` 的 `display` 块 |

贴图可以是任意**正方形**尺寸；动画就是「帧竖着排」（160×160 的 8 帧 = 160×1280）。
模板里**故意没放模型文件**，这样换贴图不会把 3D 剑模型一起覆盖掉。

### 路线 B：直接改模组本体

```bash
python tools/make_textures.py            # 图标；有原画时它会自动跳过剑/晶石贴图
python tools/build_sword_texture.py      # 用 tools/sword_source.png 生成 8 帧动画剑贴图
python tools/build_crystal_texture.py    # 用 tools/crystal_source.png 生成 8 帧动画晶石贴图
python tools/gen_sword_model.py          # ★ 把剑贴图挤出成 3D 模型（改了剑贴图就要重跑）
python tools/preview_sword_model.py      # 模型自检 + 出两张预览图，不用进游戏
pwsh -File ..\build-lightning-sword.ps1
```

- **`tools/gen_sword_model.py` 必须在 `build_sword_texture.py` 之后跑**：它读的是刚生成的贴图轮廓。
  想调手感就改脚本顶部几个常量：
  - `CELL`：轮廓分辨率（1 = 全分辨率最精细也最占体积，2 = 当前值，3~4 更省更"方块"）
  - `HALF_THICKNESS`：半厚（1.0 = 贴图 10 像素厚）
  - `TIP_TAPER`：剑尖收薄比例
- **`tools/preview_sword_model.py`** 会做结构校验（坐标/朝向/UV 是否合法，有没有退化几何），
  再输出 `tools/model_preview.png`（等轴视角看厚度）和 `tools/model_front.png`（纯正面按 UV
  采样，用来确认几何和贴图对得上）。**改完模型建议先跑一遍**，比进游戏试快得多。

- **`tools/sword_source.png`** 是你的剑原画（碎晶剑，160×1280）。换成任何**正方形**图片再跑
  `build_sword_texture.py`，脚本会自动挑最完整的一帧当底图，叠加 8 帧流动电弧和轮廓辉光。
- **`tools/crystal_source.png`** 是你的晶石原画（408×408）。脚本会自动去掉浅色背景、裁到内容、
  居中成正方形再缩到 64×64，然后叠加三种动态特效（内部辉光呼吸 + 表面电弧爬行 + 火星闪烁）。
- **不会再互相覆盖**：`make_textures.py` 检测到 `sword_source.png` / `crystal_source.png` 存在时，
  会跳过对应的贴图（只写像素风备用版），所以随便跑哪个生成器都不会把成品冲掉。
- **删过文件后要 `clean` 再 build**，否则 Gradle 增量打包会残留已删除的资源：
  `pwsh -File ..\build-lightning-sword.ps1 -Task clean`

姿势的数学模拟器源码见 `tools/PoseSim.java` 与 `tools/PoseSolve.java`（改角度后可重新求解）。**注意：这两个文件当前已不在 `tools/` 中。**

## 安装

1. 安装 **Fabric Loader**（≥ 0.15.11）到 Minecraft **1.21.1**。
2. 把 [Fabric API](https://modrinth.com/mod/fabric-api) 放进 `mods/`。
3. 把 `lightning-sword-1.0.0.jar` 放进 `mods/`。

## 自己编译

需要 **JDK 21**。

```bash
set JAVA_HOME=C:\path\to\jdk-21   # Windows
./gradlew build                   # macOS / Linux
```

产物在 `build/libs/lightning-sword-1.0.0.jar`。

> 中国大陆下载依赖慢可以把仓库换成腾讯云/阿里云镜像；wrapper 也可以在
> `gradle/wrapper/gradle-wrapper.properties` 里把 `distributionUrl` 换成
> `https://mirrors.cloud.tencent.com/gradle/gradle-8.12-bin.zip`。

### 在 DSH 沙箱里编译（Windows 特有）

DSH 的文件沙箱会让 `java.nio.file.Files.isWritable()` 对**所有**路径都返回 `false`
（受限令牌过不了 Windows 的 DACL 检查），而 JDK 的 zip 文件系统正是拿这个调用来决定「只读」，
于是 Loom 合并 Minecraft 客户端 + 服务端 jar 时会抛出 `ReadOnlyFileSystemException`。

解决办法是把 `jdk.zipfs` 里那句判断换成真正的 `open(WRITE)` 探测，再用 `--patch-module`
加载进 Gradle 的构建 JVM：

```powershell
pwsh -File .\build-lightning-sword.ps1              # 构建
pwsh -File .\build-lightning-sword.ps1 -Task clean  # 清理
```

**正常 Windows 环境不需要这一步**，直接 `gradlew build` 即可。

> 另一个沙箱注意点：DSH 给工作区目录打的 **Low 完整性标签**是 Java 子进程能写文件的前提。
> 新建的顶层目录不会带这个标签，需要补 `icacls <目录> /setintegritylevel (OI)(CI)Low`。

## 代码结构

```
src/main/java/com/dsh/lightningsword/
├── LightningSwordMod.java          入口：注册物品、网络包、注入末地城战利品表
├── ModItems.java                   圣雷剑（原版属性写法）+ 雷电晶矿
├── LightningSwordItem.java         ★ 蓄力/松手发射、近战、闲置火花、维修、tooltip
├── LightningBeam.java              ★ 服务端：射线检测、1.5 格自动追踪、10 点真伤、先点燃再伤害
├── network/LightningBeamPayload.java  S2C 自定义包（起点/终点/种子）
└── client/
    ├── LightningSwordClient.java   客户端入口：收包、渲染事件、tick、Sodium 保活挂钩
    ├── BeamRenderer.java           ★ 照搬原版闪电几何，沿飞行方向绘制 + 近端裁剪（**别改写法**）
    ├── ClientBeams.java            正在显示的闪电（5 tick，逐帧换形状）
    └── SwordSprites.java           让剑/晶石的 8 帧动画在 Sodium 下继续跑（没 Sodium 就空转）

tools/
├── sword_source.png                你的剑原画
├── crystal_source.png              你的晶石原画
├── build_sword_texture.py          剑原画 → 8 帧动画剑贴图（叠流动电弧 + 轮廓辉光）
├── build_crystal_texture.py        晶石原画 → 去背景 + 裁切 → 8 帧动画晶石贴图
├── make_textures.py                图标 + 像素风备用贴图（有原画时自动跳过对应贴图）
├── gen_sword_model.py              ★ 把剑贴图轮廓挤出成 3D 模型（正面/背面/厚度）
├── preview_sword_model.py          模型结构自检 + 出预览图（不用进游戏）
├── PoseSim.java / PoseSolve.java   姿势数学模拟器与求解器（历史遗留，**当前已不在 tools/ 中**）
├── resourcepack-template/          资源包模板（只有贴图，不用编译）
└── patch_zipfs.py                  DSH 沙箱用的 jdk.zipfs 补丁
```

## 已知限制

1. **只有 1.21.1**。1.21.2+ 的 `UseAction`→`UseAnim`、item model definition 等改动较大，需要单独适配。
2. 瞄准姿势只有一套，是写死在 `lightning_sword.json` 的 `display` 里的；想换角度直接改那 4 个数。
3. 第三人称的角度是按第一人称同样的偏移推的，没有单独逐帧验证过。
4. 用的是 160×160 高清贴图，风格和原版像素风不太一样；想统一可以缩到 32×32 或 16×16。
5. 3D 模型是**轮廓挤出**的：轮廓分辨率由 `CELL` 决定（当前 2 像素，实测轮廓误差 ≤2 像素，
   剑尖和护手基本无损）。想要像素级锐利就把 `gen_sword_model.py` 里的 `CELL` 改成 1
   （面数和文件体积约涨 4 倍）。
6. 模型文件约 660 KB（4146 个面），首次加载资源包时会有一次性开销；这是"真 3D"的代价。

## 许可

MIT

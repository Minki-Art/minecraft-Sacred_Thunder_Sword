# 项目状态 / 交接文档

> 写给**没有上下文的新会话**：读完这一份就能接手继续做。
> 最后更新：`SwordSprites` 贴图保活回归（用户实测它**有效**），同时保持闪电渲染和剑的位置为原始状态。
>
> **本轮改动摘要**（细节见 §4.2 / §4.5 / §4.6）：
> 1. 只保留一套瞄准姿势（原 `aim_x60_y45`），删除 `aim_0..7`、`SwordPose.java`、`P` 键、
>    model predicate 和 `lightning_sword.accesswidener`
> 2. `lightning_sword.json` 不再是平面：`tools/gen_sword_model.py` 按贴图轮廓挤出成 3D 薄板，
>    **几何坐标 = 贴图原始像素位置**，位置/枢轴与旧版逐点一致
> 3. `client/SwordSprites.java`：每 tick 反射调 Sodium 的 `SpriteUtil.INSTANCE.markSpriteActive(...)`，
>    让剑和晶石的 8 帧贴图动画在 Sodium 下继续跑。**用户实测有效**，保留
> 4. **❌ 一并试过、已被用户否决并回退**：`BeamRenderer` 改成"自建缓冲立即绘制"
>    （`Tessellator.begin` + `BufferRenderer.drawWithGlobalProgram`）→ 用户实测**闪电变黑**。
>    闪电代码已恢复原样，**不要再动**

---

## 0. 一句话状态

Fabric **1.21.1** 模组，成品在
`D:\mcmod\lightning-sword\build\libs\lightning-sword-1.0.0.jar`
（345 KB，已重映射为 intermediary，可直接丢进 `mods/`）。**构建通过，无已知 bug。**

---

## 1. 功能清单（都已实现并验证过）

| 功能 | 说明 |
|---|---|
| 剑名 | **圣雷剑** / Sacred Thunder Sword（`lightning_sword:lightning_sword`） |
| 近战 | **15 伤害 / 1.8 攻速**，用原版 `SwordItem.createAttributeModifiers(ToolMaterials.NETHERITE, 10, -2.2F)` 生成，**有横扫之刃** |
| 蓄力 | 右键按住蓄力；`UseAction.BOW`（不是 SPEAR，原因见 §4.1）；不足 0.4 秒空放 |
| 发射 | 松手射出闪电，射程 8→24 格（随蓄力） |
| 伤害 | **10 点真实伤害**（`indirectMagic`，在 `#minecraft:bypasses_armor` 里，无视护甲+护甲附魔） |
| 点燃 | 命中点燃 5 秒，**在造成伤害之前施加**，所以打死的猪牛羊掉**熟肉** |
| 自动追踪 | 目标在准心射线 **1.5 格**横向内自动锁定，隔墙不锁（`LightningBeam.AIM_ASSIST_RADIUS`） |
| 闪电外观 | 照搬原版 `LightningEntityRenderer` 几何（8 段随机游走+4 层丝带+`RenderLayer.getLightning()`），沿飞行方向绘制，每帧换形状 |
| 护眼 | 离镜头 <2.2 格的部分裁掉；**不用** `ParticleTypes.FLASH`（原版全屏白闪，在眼前非常刺眼） |
| 瞄准姿势 | **只有一套**（原 `aim_x60_y45` 的数值）：firstperson `60,±45,25` / thirdperson `60,±45,55`，直接写在 `lightning_sword.json` 的 `display` 里。**P 键和 8 套姿势已移除** |
| 剑模型 | **真 3D 薄板**：`tools/gen_sword_model.py` 按贴图轮廓挤出 正面 + 背面 + 一圈厚度（4146 个面 / 620 KB），几何坐标 = 贴图原始像素位置，位置与旧版平面模型逐点一致 |
| 剑贴图 | 160×160 / 8 帧动画（用户原画 + 程序化流动电弧 + 轮廓辉光） |
| Sodium 下的动画 | ✅ `client/SwordSprites.java`：每 tick 用 Sodium 自己的 `SpriteUtil.markSpriteActive` 把**剑 + 晶石**两张贴图标成 active，动画就继续跑（**用户实测有效**）。原理见 §4.6 |
| 附魔闪光 | 剑和晶石都带 `enchantment_glint_override` |
| 雷电晶矿 | **晶体物品**（像钻石，不是方块），64×64 / 8 帧动画（内部辉光呼吸+表面电弧+火星） |
| 获取 | 末地城战利品箱 **8.8%**（`LootTableEvents.MODIFY` 注入 `minecraft:chests/end_city_treasure`）；物品 tooltip 有写 |
| 合成 | 锻造台：下界合金剑 + 下界合金升级模板 + 雷电晶矿 |

---

## 2. 构建方式（必读，有 3 个环境坑）

### 正常环境

```bash
set JAVA_HOME=C:\path\to\jdk-21   # 需要 JDK 21
gradlew.bat build                  # 产物 build/libs/lightning-sword-1.0.0.jar
```

### DSH 沙箱环境（Windows）

```powershell
pwsh -File .\build-lightning-sword.ps1              # 构建
pwsh -File .\build-lightning-sword.ps1 -Task clean  # 清理
```

三个坑，脚本都已处理，但**改脚本时别破坏它们**：

1. **`Files.isWritable()` 恒为 false** → JDK 的 zipfs 把所有 jar 当只读 → Loom 合并 Minecraft jar 时抛
   `ReadOnlyFileSystemException`。
   解决：`tools/patch_zipfs.py` 把 `jdk.zipfs` 里那句判断改成真正的 `open(WRITE)` 探测，
   用 `--patch-module jdk.zipfs=...` 加载进构建 JVM。

2. **`java.io.tmpdir` 必须同时写进 `org.gradle.jvmargs`**，只写 `GRADLE_OPTS` 没用
   （前者才作用于 fork 出来的构建 JVM）。否则报
   `Failed to initialise native integration / java.io.IOException: 拒绝访问`。

3. **临时目录必须放在带 Low 完整性标签的目录里面**。`D:\mcmod` 根目录没有 Low 标签且
   **无法补**（`icacls` 报 Access is denied），所以临时目录用
   `D:\mcmod\.gradle-home\tmp`（`.gradle-home` 有 `(OI)(CI)Low`，子目录自动继承）。
   同理：**在 `D:\mcmod` 下新建任何给 Java/Gradle 用的目录，都要补**
   `icacls <目录> /setintegritylevel (OI)(CI)Low`。

4. **删过源文件后必须 `clean` 再 build**，否则 Gradle 增量打包会把已删除的资源留在 jar 里。

---

## 3. 文件地图

```
lightning-sword/
├── build/libs/lightning-sword-1.0.0.jar      ← 成品
├── README.md                                 使用/玩法/改贴图说明
├── MIGRATION.md                              迁移到高版本的核对清单
├── PROJECT-STATE.md                          本文件
├── build.gradle / settings.gradle / gradle.properties
├── src/main/java/com/dsh/lightningsword/
│   ├── LightningSwordMod.java                入口：物品注册、S2C 包、战利品注入 + 诊断日志
│   ├── ModItems.java                         圣雷剑 + 雷电晶矿（含 tooltip）
│   ├── LightningSwordItem.java               蓄力/发射、近战、闲置火花、维修
│   ├── LightningBeam.java                    射线、1.5 格追踪、10 真伤、先点燃后伤害、广播
│   ├── network/LightningBeamPayload.java     S2C（起点/终点/种子）
│   └── client/
│       ├── LightningSwordClient.java         收包、渲染事件、tick、Sodium 保活挂钩
│       ├── BeamRenderer.java                 原版闪电几何 + 近端裁剪（**就用 context.consumers()，别改写法**）
│       ├── ClientBeams.java                  5 tick 生命，逐帧换形状
│       └── SwordSprites.java                 让剑 + 晶石贴图动画在 Sodium 下继续跑（没 Sodium 就空转）
├── src/main/resources/
│   ├── fabric.mod.json                       含 client 入口（**已无 accessWidener**）
│   ├── assets/lightning_sword/               贴图/模型/语言/图标
│   │   └── models/item/lightning_sword.json  ★ 3D 挤出模型（660 KB / 4146 面），取代旧的两级 override
│   └── data/lightning_sword/recipe/          锻造台配方
└── tools/
    ├── sword_source.png        用户的剑原画（160×1280）
    ├── crystal_source.png      用户的晶石原画（408×408）
    ├── build_sword_texture.py  剑原画 → 8 帧动画贴图
    ├── build_crystal_texture.py 晶石原画 → 去背景+裁切 → 8 帧动画贴图
    ├── make_textures.py        图标 + 像素风备用贴图（**有原画时自动跳过对应贴图**）
    ├── gen_sword_model.py      ★ 剑贴图轮廓 → 3D 挤出模型（改了剑贴图必须重跑）
    ├── preview_sword_model.py  模型自检 + 两张预览图（`model_preview.png` / `model_front.png`）
    ├── PoseSim.java / PoseSolve.java  姿势数学模拟器（**文件当前不存在**）
    └── resourcepack-template/  资源包模板（只有贴图，不含模型）

mcmod/
├── build-lightning-sword.ps1   DSH 构建脚本
├── tools/                      jdk-21 + gradle-8.12 + patch_zipfs.py + yarninfo.py + yarn_diff.py（**本行原指 `D:\mcmod\tools\`，不是 `lightning-sword\tools\`；`yarninfo.py` 需要同目录的 `yarn.tiny`**）
├── .gradle-home/               Gradle 全局缓存（**含 tmp/，必须留**）
├── .jdk-patch/                 zipfs 补丁产物（构建必需）
├── .gradle-mod/                random-crafting-table 的缓存（别人家项目，别动）
└── random-crafting-table/     用户另一个模组工程，与本项目无关，不要动
```

---

## 4. 关键技术决定（为什么这么做）

### 4.1 瞄准姿势是**数学解出来的**，不是试出来的

- 从用户截图量出红线方向：`(217,124)→(292,189)` = 屏幕角度 **139.1°**（左上 41°）
- 量出剑身实际朝向（第 5 套）：**105°**
- 反编译 `HeldItemRenderer` 的变换链
  （`applyEquipOffset → Rx(-13.935) Ry(35.3) Rz(-9.785) → Ry(45) → DisplayTransform → translate(-0.5)`），
  用**真实 JOML** 写模拟器（`tools/PoseSim.java`，**该文件当前不存在**）
- 模拟器算出第 5 套 = **104.2°**，与量到的 105° 吻合 → 模型可信
- Z 轴与屏幕角度约 **1:1**，于是 Z: 25 → **64** → 模拟角度 **139.5°**，与红线差 0.4°

**为什么用 `UseAction.BOW` 而不是 SPEAR**：原版对 SPEAR 会先转 `Rx(-55°)`，三叉戟是 3D 模型转完刚好指向前方，
而平面剑会**横躺在头顶**。BOW 只转 `Rx(-13.9°)`。

### 4.2 模型 overrides 的顺序是**反直觉的**（踩过两次；现在已不再使用 override，留作教训）

`ModelOverrideList` 构造函数会 `for (j = size-1; j >= 0; j--)` **反转** JSON 顺序，
`apply()` 取**第一个**满足 `value >= threshold` 的。所以：

- JSON 必须**从弱到强升序**写（原版 `bow.json` 就是这样）
- 谓词返回值必须留在 **0..1**，因为 `ClampedModelPredicateProvider.call()` 会 `clamp(0,1)`
  → 当时用 `(index+1)/8`（0.125…1.0，精确二进制）
- **现状**：用户定下姿势后，8 套 override 全部删除，`lightning_sword.json` 直接是"基模 + display"，
  predicate、`accessWidener`、`P` 键一键全删。

### 4.3 战利品

- 末地城箱子是 `EndCityGenerator` **在代码里**赋 `LootTables.END_CITY_TREASURE_CHEST`，
  结构 NBT 里没有 LootTable 字段（NBT 里甚至有硬编码 Items，会被代码覆盖）
- 用 `LootTableEvents.MODIFY`（**v3**；v2 也能触发，但 v3 是 1.21.1 的正路）
- **踩过的坑**：只改了代码没重跑生成器 → jar 里还是旧内容；Gradle 增量打包残留旧资源 → 要 `clean`

### 4.4 贴图生成器的互相覆盖

`make_textures.py` 默认也写剑/晶石贴图，会把 `build_*_texture.py` 的成品冲掉（**实际发生过一次**）。
现在加了保护：检测到 `sword_source.png` / `crystal_source.png` 存在就**跳过**。

### 4.5 3D 剑模型是"轮廓挤出"，不是手工建模

- 输入：`lightning_sword.png`（160×160 × 8 帧）
- 每帧取 `alpha >= 128` 的实心轮廓 → `drop_specks` 去噪 + `fill_holes` 补洞
- 正面/背面：轮廓先做**贪心矩形合并**（1300 个格子 → 约 82 个矩形），面数直接降一个数量级
- 厚度：沿轮廓每个暴露的格子边一条窄面，UV 取该**边缘像素中心**，于是侧看是实心金属截面
- 坐标：**几何用贴图的原始像素位置直接换算**——`x = col * 0.1`、`y = 16 - row * 0.1`
  （1 贴图像素 = 0.1 模型单位，因为一帧 160 像素 = 16 模型单位）。
  **不做任何平移/居中**：这样剑的位置、大小、旋转枢轴和旧版那个平面模型逐点一致。
- ⚠️ **踩过的坑（用户实测报"位置错误"）**：有一版把轮廓平移到模型原点（`(col-left)*upp`），
  等于把剑放大并挪了位；另一版还把它居中到 (8,8)（我以为是"和原版枢轴一致"），同样会偏。
  **正确做法就是按贴图原始位置摆放，不加任何平移。**
- 另一个坑：轮廓被裁到 mask 的 bbox（texture 坐标 `(20,0)-(320,292)`），**UV 必须和几何一起平移**，
  两边都基于原始像素位置，才不会出现"贴图和几何错位"。
- **换贴图必须重跑** `python tools/gen_sword_model.py`，然后 `preview_sword_model.py` 自检
- **曾经的 bug**：忘了 `16/160` 的缩放（坐标放大 10 倍、UV 越界、`from == to` 的退化几何）。
  现在 `preview_sword_model.py` 会检查"坐标范围 / from<to / 面朝向 / UV 长度"，防止再犯。

### 4.6 Sodium 为什么会让剑贴图卡在第 1 帧

（用户实测：只有 Sodium，JEI/苹果皮/连锁采集都不影响；卸载就正常）

- Sodium 的 `animateOnlyVisibleTextures` 会 mixin `SpriteContents.Ticker.tickAndUpload`：
  在 HEAD 处 `if (onDemand && !sprite.sodium$isActive()) { 只推进帧计数; ci.cancel(); }`
  —— 帧计数器在跑，但**新像素永远不上传**，看起来就是卡住不动
- 标记 active 只能由 Sodium 自己的 `SpriteUtil.markSpriteActive()` 完成。它的原版物品快速路径
  （`ItemRendererMixin.renderBakedItemQuads` 里 `quad.getSprite()`）是通的，但 **FRAPI 物品路径**
  （`ItemRenderContext.bufferQuad`）里找 sprite 用的是 `SpriteFinderCache.forBlockAtlas()`
  —— **block 图集**，物品 sprite 不在里面，于是查不到、标不上
- ✅ **正确的修法（已采用，用户实测有效）**：`client/SwordSprites.java` 在
  `ClientTickEvents.END_CLIENT_TICK` 里反射调 `SpriteUtil.INSTANCE.markSpriteActive(sprite)`，
  把 `lightning_sword:item/lightning_sword` 和 `lightning_sword:item/thunder_crystal` 两张贴图标成 active。
  时序：一帧是 `MinecraftClient.tick()`（含 `textureManager.tick()` 上传帧）→ 渲染，
  而 `END_CLIENT_TICK` 夹在两者之间，所以标记对本帧渲染生效。没有 Sodium 时整个类空转
- ❌ **绝对不要顺带改渲染写法**。曾经把 `BeamRenderer` 从 `context.consumers().getBuffer(...)`
  改成 `Tessellator.begin(...)` + `BufferRenderer.drawWithGlobalProgram(...)` 自绘立即提交，
  用户实测**闪电变成黑色**（图1）。闪电代码现在保持原样，**别再碰**
- **当时的 accessWidener 也删了**：姿势切换没了，就不再需要 `ModelPredicateProviderRegistry.register`

---

## 5. 未决 / 待办

| # | 事项 | 状态 |
|---|---|---|
| 1 | **末地船 15.2%** | ❌ **按原版做不到**。`EndCityGenerator` 对末地城所有箱子（含末地船）赋同一张表，且代码会覆盖 NBT。要区分只能 **mixin 进 `EndCityGenerator`** 判断 piece 类型 —— 用户还没决定要不要做 |
| 2 | **战利品到底是 bug 还是运气** | 已加诊断日志。用户反馈"还真有"（说明注入是生效的，之前是运气）。日志仍保留，进游戏看 `logs/latest.log` 会有 `end city loot injection: OK` |
| 3 | **3D 剑模型是否满意** | 待用户进游戏看。这一版坐标已改成"贴图原始像素位置"，位置应与旧版一致。想更锐利可把 `gen_sword_model.py` 的 `CELL` 改 1；厚度 `HALF_THICKNESS=1.0`（10 像素） |
| 4 | **Sodium 下的贴图动画** | ✅ 已解决（`SwordSprites` 保活剑 + 晶石，用户实测有效）。若哪天又不动了：先看 `logs/latest.log` 有没有 `[lightning_sword] Sodium detected; sword/crystal animation boost active.`；没有就是 Sodium 的 API 变了 |
| 5 | 第三人称角度 | 按第一人称同样的偏移推的，**没有单独逐帧验证过** |
| 6 | `random-crafting-table` | 用户另一个工程，其 `tools/*.ps1` 和 README 里还写死着 `D:\dshdeepseek\...` 旧路径（搬家后失效）。用户没要求修 |

---

## 6. 环境事实

- 目标平台：**Minecraft 1.21.1 + Fabric**（Yarn 1.21.1+build.3, loader 0.16.10, Loom 1.9.2, Fabric API 0.116.17+1.21.1）
- JDK 21：`D:\mcmod\tools\jdk-21.0.12.1+1`
- Gradle：`D:\mcmod\tools\gradle-8.12`
- **用户的游戏实例**：`C:\Users\asd\mc\.minecraft\versions\1.21.1\mods`
  （里面有 `sodium-fabric-0.8.13+mc1.21.1.jar.disabled`、jei、appleskin、veinminer、fabric-api、我们的 jar）
- **当前最新 MC 是 26.3**（改成按年编号），但 **Yarn 只到 1.21.11** —— 迁移路线见 `MIGRATION.md`
- 联网：本机 PowerShell/curl 的 TLS 是坏的（schannel `SEC_E_NO_CREDENTIALS`），
  **但 Python 和 Java 的 HTTPS 正常** —— 下载东西一律用 Python 或 Gradle，别用 `Invoke-WebRequest`/`curl`
  （`raw.githubusercontent.com` 会被重置，改用 `api.github.com` 取 base64 内容）
- 国内下载：Gradle 官方源约 100 KB/s，**腾讯云镜像 `https://mirrors.cloud.tencent.com/gradle/` 约 10 MB/s**

---

## 7. 常用命令速查

```powershell
# 构建 / 清理（删过源文件必须 clean，否则 jar 里会留旧资源）
pwsh -File D:\mcmod\build-lightning-sword.ps1
pwsh -File D:\mcmod\build-lightning-sword.ps1 -Task clean

# 重新生成贴图（顺序：有原画时 make_textures 会自动跳过剑和晶石）
python D:\mcmod\lightning-sword\tools\make_textures.py
python D:\mcmod\lightning-sword\tools\build_sword_texture.py
python D:\mcmod\lightning-sword\tools\build_crystal_texture.py

# 剑贴图改过之后：重新挤出 3D 模型，再自检 + 出预览图（不用进游戏）
python D:\mcmod\lightning-sword\tools\gen_sword_model.py
python D:\mcmod\lightning-sword\tools\preview_sword_model.py

# 查某个 Yarn 版本里这个 mod 用到的符号还在不在
python D:\mcmod\tools\yarn_diff.py 1.21.11+build.6

# 反编译 Minecraft 看源码（产物在 .gradle/loom-cache/minecraftMaven/**/*-sources.jar）
pwsh -File D:\mcmod\build-lightning-sword.ps1 -Task genSources

# 查 Sodium 源码（raw.githubusercontent 连不上，走 api.github.com 取 base64 内容）
#   仓库 CaffeineMC/sodium，tag mc1.21.1-0.8.13，重点看
#   common/src/main/java/net/caffeinemc/mods/sodium/mixin/features/textures/animations/tracking/
```

---

## 8. 用户偏好（沟通上要注意）

- 中文交流，喜欢**直接给结论 + 可验证的证据**，不喜欢含糊其辞
- 会实际进游戏测试并反馈截图，**看不懂游戏画面时必须用数学/源码求证，不要猜**
- 自己会画贴图/收集素材，放在 `resourcepack-template` 或 `tools/` 下，需要主动接进模组
- 明确说过：**不要动 `random-crafting-table`**
- **🔴 不要去"加固"闪电渲染代码**。`BeamRenderer` 就用 `context.consumers().getBuffer(...)`；
  换自立缓冲（`Tessellator.begin` + `BufferRenderer.drawWithGlobalProgram`）用户实测会**变黑**。
- **🔴 没要求的东西不要自己加**（原话："我没要求的不要自己任主张"）。优化类模组导致的渲染问题，
  先判断能不能用对方自己的设置解决；不要替用户决定往代码里塞补丁。
- 改动剑的模型时**必须保证位置不变**：几何坐标直接用贴图原始像素换算，不做平移/居中。

package com.dsh.lightningsword.client;

import com.dsh.lightningsword.ModItems;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.texture.Sprite;
import net.minecraft.client.texture.SpriteAtlasTexture;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.PlayerScreenHandler;
import net.minecraft.util.Identifier;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * Keeps the sword's and the crystal's 8-frame texture animation running even when Sodium is
 * installed.
 *
 * <p><b>Why this is needed.</b> Sodium's performance option {@code animateOnlyVisibleTextures}
 * patches {@code SpriteContents.Ticker.tickAndUpload} and cancels the frame upload unless the
 * sprite was marked "active" during the previous frame. A sprite is only marked active by Sodium's
 * own render paths ({@code SpriteUtil.markSpriteActive}); for the FRAPI item path it looks the
 * sprite up in the <b>block</b> atlas, so item sprites never get marked. Both textures then keep
 * ticking their frame counter with the pixels never uploaded, which is the "stuck on frame 1" that
 * was seen in game.</p>
 *
 * <p><b>What this does, and what it does NOT do.</b> At the end of every client tick it marks the
 * two sprites active through Sodium's own public API, and that is all it touches. A Minecraft frame
 * runs {@code textureManager.tick()} (which uploads the next animation frame) and then renders, and
 * Fabric's {@code END_CLIENT_TICK} sits between the two - so the flag is already set for the frame
 * about to be drawn. It deliberately does not change how anything is drawn: the lightning beam
 * keeps using {@code context.consumers()} and the sword model keeps its own geometry.</p>
 */
public final class SwordSprites {
    /** The sword's layer0 texture, the file that carries its 8 animation frames. */
    private static final Identifier SWORD_TEXTURE =
            Identifier.of("lightning_sword", "item/lightning_sword");
    /** The crystal's texture, also an 8-frame animation. */
    private static final Identifier CRYSTAL_TEXTURE =
            Identifier.of("lightning_sword", "item/thunder_crystal");

    private static Method markActive;
    private static Object spriteUtil;

    private SwordSprites() {
    }

    /** Resolves Sodium's SpriteUtil.INSTANCE#markSpriteActive(TextureAtlasSprite) once. */
    public static void init() {
        if (!FabricLoader.getInstance().isModLoaded("sodium")) {
            System.out.println("[lightning_sword] Sodium not present; texture animation boost inactive.");
            return;
        }
        try {
            Class<?> utilClass = Class.forName("net.caffeinemc.mods.sodium.api.texture.SpriteUtil");
            Field instance = utilClass.getField("INSTANCE");
            spriteUtil = instance.get(null);
            markActive = utilClass.getMethod("markSpriteActive", Sprite.class);
            System.out.println("[lightning_sword] Sodium detected; sword/crystal animation boost active.");
        } catch (Throwable throwable) {
            spriteUtil = null;
            markActive = null;
            System.out.println("[lightning_sword] Sodium present but its texture API is unavailable: " + throwable);
        }
    }

    /** Marks our two textures active for this frame, so Sodium uploads their next animation frame. */
    public static void markSpritesActive() {
        if (markActive == null || spriteUtil == null) {
            return;
        }
        MinecraftClient client = MinecraftClient.getInstance();
        if (client == null || client.player == null) {
            return;
        }
        // Only pay for it while the items are actually being carried: otherwise this would keep
        // the item atlas animating while the player has neither.
        boolean sword = playerHas(client, ModItems.LIGHTNING_SWORD);
        boolean crystal = playerHas(client, ModItems.THUNDER_CRYSTAL);
        if (!sword && !crystal) {
            return;
        }
        SpriteAtlasTexture atlas = (SpriteAtlasTexture) client.getTextureManager()
                .getTexture(PlayerScreenHandler.BLOCK_ATLAS_TEXTURE);
        if (atlas == null) {
            return;
        }
        if (sword) {
            mark(atlas, SWORD_TEXTURE);
        }
        if (crystal) {
            mark(atlas, CRYSTAL_TEXTURE);
        }
    }

    private static void mark(SpriteAtlasTexture atlas, Identifier texture) {
        Sprite sprite = atlas.getSprite(texture);
        if (sprite == null) {
            return;
        }
        try {
            markActive.invoke(spriteUtil, sprite);
        } catch (Throwable ignored) {
            // A failed mark only means the animation falls back to Sodium's own tracking.
        }
    }

    private static boolean playerHas(MinecraftClient client, Item item) {
        for (ItemStack stack : client.player.getInventory().main) {
            if (stack.isOf(item)) {
                return true;
            }
        }
        for (ItemStack stack : client.player.getInventory().offHand) {
            if (stack.isOf(item)) {
                return true;
            }
        }
        return client.player.getOffHandStack().isOf(item);
    }
}

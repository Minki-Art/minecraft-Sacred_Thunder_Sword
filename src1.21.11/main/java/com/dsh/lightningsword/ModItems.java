package com.dsh.lightningsword;

import net.minecraft.item.Item;
import net.minecraft.item.ToolMaterial;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.tag.TagKey;
import net.minecraft.util.Rarity;
import net.minecraft.registry.Registry;
import net.minecraft.registry.Registries;
import net.minecraft.component.DataComponentTypes;
import net.minecraft.item.Item.Settings;

public final class ModItems {
   /**
    * Since 1.21.9 an item has to know its own registry key before it is constructed:
    * {@code Item.Settings} carries it and {@link Item}'s constructor throws
    * {@code NullPointerException: Item id not set} without it. The key also feeds the default
    * translation key and the item model id, so it has to be built from the same identifier.
    */
   public static final RegistryKey<Item> LIGHTNING_SWORD_KEY =
      RegistryKey.of(RegistryKeys.ITEM, LightningSwordMod.id("lightning_sword"));
   public static final RegistryKey<Item> THUNDER_CRYSTAL_KEY =
      RegistryKey.of(RegistryKeys.ITEM, LightningSwordMod.id("thunder_crystal"));

   /**
    * What the sword accepts for repair: the thunder crystal, plus the netherite tool
    * material tag that the tool material itself contributes.
    */
   public static final TagKey<Item> REPAIRS_LIGHTNING_SWORD =
      TagKey.of(RegistryKeys.ITEM, LightningSwordMod.id("repairs_lightning_sword"));

   public static final Item LIGHTNING_SWORD = new LightningSwordItem(
      new Settings()
         .registryKey(LIGHTNING_SWORD_KEY)
         .maxCount(1)
         .rarity(Rarity.EPIC)
         .fireproof()
         .component(DataComponentTypes.ENCHANTMENT_GLINT_OVERRIDE, true)
         .sword(ToolMaterial.NETHERITE, 10.0F, -2.2F)
         .repairable(REPAIRS_LIGHTNING_SWORD)
   );
   public static final Item THUNDER_CRYSTAL = new ThunderCrystalItem(
      new Settings()
         .registryKey(THUNDER_CRYSTAL_KEY)
         .rarity(Rarity.RARE)
         .component(DataComponentTypes.ENCHANTMENT_GLINT_OVERRIDE, true)
   );

   private ModItems() {
   }

   public static void register() {
      Registry.register(Registries.ITEM, LIGHTNING_SWORD_KEY, LIGHTNING_SWORD);
      Registry.register(Registries.ITEM, THUNDER_CRYSTAL_KEY, THUNDER_CRYSTAL);
   }
}

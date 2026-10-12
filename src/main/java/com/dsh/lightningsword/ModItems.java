package com.dsh.lightningsword;

import net.minecraft.item.Item;
import net.minecraft.item.ToolMaterial;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.tag.TagKey;
import net.minecraft.util.Rarity;
import net.minecraft.registry.Registry;
import net.minecraft.registry.Registries;
import net.minecraft.component.DataComponentTypes;
import net.minecraft.item.Item.Settings;

public final class ModItems {
   /**
    * What the sword accepts for repair: the thunder crystal, plus the netherite tool
    * material tag that the tool material itself contributes.
    */
   public static final TagKey<Item> REPAIRS_LIGHTNING_SWORD =
      TagKey.of(RegistryKeys.ITEM, LightningSwordMod.id("repairs_lightning_sword"));

   public static final Item LIGHTNING_SWORD = new LightningSwordItem(
      new Settings()
         .maxCount(1)
         .rarity(Rarity.EPIC)
         .fireproof()
         .component(DataComponentTypes.ENCHANTMENT_GLINT_OVERRIDE, true)
         .sword(ToolMaterial.NETHERITE, 10.0F, -2.2F)
         .repairable(REPAIRS_LIGHTNING_SWORD)
   );
   public static final Item THUNDER_CRYSTAL = new ThunderCrystalItem(
      new Settings().rarity(Rarity.RARE).component(DataComponentTypes.ENCHANTMENT_GLINT_OVERRIDE, true)
   );

   private ModItems() {
   }

   public static void register() {
      Registry.register(Registries.ITEM, LightningSwordMod.id("lightning_sword"), LIGHTNING_SWORD);
      Registry.register(Registries.ITEM, LightningSwordMod.id("thunder_crystal"), THUNDER_CRYSTAL);
   }
}

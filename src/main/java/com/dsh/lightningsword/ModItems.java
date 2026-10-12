package com.dsh.lightningsword;

import net.minecraft.item.Item;
import net.minecraft.util.Rarity;
import net.minecraft.item.SwordItem;
import net.minecraft.item.ToolMaterials;
import net.minecraft.registry.Registry;
import net.minecraft.registry.Registries;
import net.minecraft.component.DataComponentTypes;
import net.minecraft.item.Item.Settings;

public final class ModItems {
   public static final Item LIGHTNING_SWORD = new LightningSwordItem(
      ToolMaterials.NETHERITE,
      new Settings()
         .maxCount(1)
         .rarity(Rarity.EPIC)
         .fireproof()
         .component(DataComponentTypes.ENCHANTMENT_GLINT_OVERRIDE, true)
         .attributeModifiers(SwordItem.createAttributeModifiers(ToolMaterials.NETHERITE, 10, -2.2F))
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

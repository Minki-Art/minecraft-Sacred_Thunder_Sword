package com.dsh.lightningsword;

import com.dsh.lightningsword.network.LightningBeamPayload;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents.ModifyEntries;
import net.fabricmc.fabric.api.loot.v3.LootTableEvents;
import net.fabricmc.fabric.api.loot.v3.LootTableEvents.Modify;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.minecraft.loot.condition.RandomChanceLootCondition;
import net.minecraft.util.Identifier;
import net.minecraft.loot.provider.number.ConstantLootNumberProvider;
import net.minecraft.loot.LootTable;
import net.minecraft.registry.RegistryKey;
import net.minecraft.loot.LootPool;
import net.minecraft.loot.entry.ItemEntry;
import net.minecraft.item.ItemGroups;
import net.minecraft.registry.RegistryKeys;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LightningSwordMod implements ModInitializer {
   public static final String MOD_ID = "lightning_sword";
   public static final Logger LOGGER = LoggerFactory.getLogger("lightning_sword");
   private static final float END_CITY_CRYSTAL_CHANCE = 0.088F;
   private static final RegistryKey<LootTable> END_CITY_TREASURE = RegistryKey.of(
      RegistryKeys.LOOT_TABLE, Identifier.ofVanilla("chests/end_city_treasure")
   );

   public static Identifier id(String path) {
      return Identifier.of("lightning_sword", path);
   }

   public void onInitialize() {
      ModItems.register();
      PayloadTypeRegistry.playS2C().register(LightningBeamPayload.ID, LightningBeamPayload.CODEC);
      ItemGroupEvents.modifyEntriesEvent(ItemGroups.COMBAT).register((ModifyEntries)entries -> entries.add(ModItems.LIGHTNING_SWORD));
      ItemGroupEvents.modifyEntriesEvent(ItemGroups.INGREDIENTS).register((ModifyEntries)entries -> entries.add(ModItems.THUNDER_CRYSTAL));
      LootTableEvents.MODIFY
         .register(
            (Modify)(key, tableBuilder, source, registries) -> {
               if (END_CITY_TREASURE.equals(key)) {
                  tableBuilder.pool(
                     LootPool.builder()
                        .rolls(ConstantLootNumberProvider.create(1.0F))
                        .with(ItemEntry.builder(ModItems.THUNDER_CRYSTAL))
                        .conditionally(RandomChanceLootCondition.builder(0.088F))
                  );
               }
            }
         );
      LOGGER.info("[Sacred Thunder Sword] ready");
   }
}

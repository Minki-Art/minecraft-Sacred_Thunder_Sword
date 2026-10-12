package com.dsh.lightningsword;

import java.util.List;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.item.Item.Settings;
import net.minecraft.item.Item.TooltipContext;

public class ThunderCrystalItem extends Item {
    public ThunderCrystalItem(Settings settings) {
        super(settings);
    }

    @Override
    public void appendTooltip(ItemStack stack, TooltipContext context, List<Text> tooltip, TooltipType type) {
        tooltip.add(Text.translatable("item.lightning_sword.thunder_crystal.tooltip3").formatted(Formatting.AQUA));
        tooltip.add(Text.translatable("item.lightning_sword.thunder_crystal.tooltip4").formatted(Formatting.AQUA));
        tooltip.add(Text.translatable("item.lightning_sword.thunder_crystal.tooltip5").formatted(Formatting.GRAY));
        tooltip.add(Text.translatable("item.lightning_sword.thunder_crystal.tooltip6").formatted(Formatting.GRAY));
    }
}
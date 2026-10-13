package com.dsh.lightningsword;

import java.util.List;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.SwordItem;
import net.minecraft.item.ToolMaterial;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.util.UseAction;
import net.minecraft.world.World;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.util.math.Vec3d;
import net.minecraft.text.Text;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.math.MathHelper;
import net.minecraft.item.Item.Settings;
import net.minecraft.item.Item.TooltipContext;

public class LightningSwordItem extends SwordItem {
   public static final int MIN_CHARGE_TICKS = 8;
   public static final int FULL_CHARGE_TICKS = 40;
   public static final int COOLDOWN_TICKS = 10;
   private static final int MAX_USE_TIME = 72000;

   public LightningSwordItem(ToolMaterial material, Settings settings) {
      super(material, settings);
   }

   public UseAction getUseAction(ItemStack stack) {
      return UseAction.BOW;
   }

   public int getMaxUseTime(ItemStack stack, LivingEntity user) {
      return 72000;
   }

   public void inventoryTick(ItemStack stack, World world, Entity entity, int slot, boolean selected) {
      if (!world.isClient() && selected && entity instanceof PlayerEntity player) {
         if (!player.isUsingItem() && world.getTime() % 5L == 0L) {
            Vec3d look = player.getRotationVec(1.0F).normalize();
            Vec3d tip = LightningBeam.origin(player, look);
            world.addParticle(ParticleTypes.ELECTRIC_SPARK, tip.x, tip.y, tip.z, 0.0, 0.0, 0.0);
         }
      }
   }

   public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
      ItemStack stack = user.getStackInHand(hand);
      if (user.getItemCooldownManager().isCoolingDown(this)) {
         return TypedActionResult.fail(stack);
      }

      user.setCurrentHand(hand);
      if (!world.isClient()) {
         world.playSound(
            null,
            user.getX(),
            user.getY(),
            user.getZ(),
            (SoundEvent)SoundEvents.ITEM_TRIDENT_RIPTIDE_1.value(),
            SoundCategory.PLAYERS,
            0.7F,
            1.8F
         );
      }

      return TypedActionResult.consume(stack);
   }

   public void usageTick(World world, LivingEntity user, ItemStack stack, int remainingUseTicks) {
      if (!world.isClient() && user instanceof PlayerEntity player) {
         chargeSparks(world, player, this.getMaxUseTime(stack, user) - player.getItemUseTimeLeft());
      }
   }

   public void onStoppedUsing(ItemStack stack, World world, LivingEntity user, int remainingUseTicks) {
      if (!world.isClient() && user instanceof PlayerEntity player) {
         int used = this.getMaxUseTime(stack, user) - remainingUseTicks;
         if (used >= 8) {
            LightningBeam.fire(world, player, chargePower(used));
            player.getItemCooldownManager().set(this, 10);
            if (!player.isCreative()) {
               stack.damage(1, player, EquipmentSlot.MAINHAND);
            }
         }
      }
   }

   public boolean canRepair(ItemStack stack, ItemStack ingredient) {
      return ingredient.isOf(ModItems.THUNDER_CRYSTAL) || super.canRepair(stack, ingredient);
   }

   public void appendTooltip(ItemStack stack, TooltipContext context, List<Text> tooltip, TooltipType type) {
      tooltip.add(Text.translatable("item.lightning_sword.lightning_sword.tooltip").formatted(Formatting.AQUA));
      tooltip.add(Text.translatable("item.lightning_sword.lightning_sword.tooltip2").formatted(Formatting.GRAY));
   }

   private static float chargePower(int usedTicks) {
      return MathHelper.clamp((usedTicks - 8) / 32.0F, 0.0F, 1.0F);
   }

   private static void chargeSparks(World world, PlayerEntity player, int usedTicks) {
      float power = chargePower(usedTicks);
      Vec3d look = player.getRotationVec(1.0F).normalize();
      Vec3d tip = LightningBeam.origin(player, look);
      Vec3d side = LightningBeam.perpendicularHorizontal(look);
      Vec3d up = new Vec3d(0.0, 1.0, 0.0);
      double angle = usedTicks * 0.45;
      double radius = 0.3 * (1.0 - 0.45 * power);
      int count = 1 + (int)(power * 3.0F);

      for (int i = 0; i < count; i++) {
         double a = angle + i * ((Math.PI * 2) / count);
         Vec3d offset = side.multiply(Math.cos(a) * radius).add(up.multiply(Math.sin(a) * radius));
         Vec3d point = tip.add(offset);
         world.addParticle(ParticleTypes.ELECTRIC_SPARK, point.x, point.y, point.z, 0.0, 0.0, 0.0);
         if (i == 0 && power > 0.15F) {
            world.addParticle(ParticleTypes.END_ROD, point.x, point.y, point.z, 0.0, 0.0, 0.0);
         }
      }

      if (power >= 1.0F && usedTicks % 4 == 0) {
         world.playSound(
            null,
            player.getX(),
            player.getY(),
            player.getZ(),
            (SoundEvent)SoundEvents.ITEM_TRIDENT_RIPTIDE_3.value(),
            SoundCategory.PLAYERS,
            0.25F,
            1.6F
         );
      }
   }
}

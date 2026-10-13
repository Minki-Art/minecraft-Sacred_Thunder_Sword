package com.dsh.lightningsword;

import com.dsh.lightningsword.network.LightningBeamPayload;
import java.util.List;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.entity.Entity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.projectile.ProjectileUtil;
import net.minecraft.world.World;
import net.minecraft.util.math.Box;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.util.math.Vec3d;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.sound.SoundEvents;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.math.MathHelper;
import net.minecraft.world.RaycastContext;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.EntityHitResult;
import net.minecraft.util.hit.HitResult.Type;
import net.minecraft.world.RaycastContext.FluidHandling;
import net.minecraft.world.RaycastContext.ShapeType;

public final class LightningBeam {
   public static final double MIN_RANGE = 8.0;
   public static final double MAX_RANGE = 24.0;
   public static final float DAMAGE = 10.0F;
   public static final float FIRE_SECONDS = 5.0F;
   public static final double AIM_ASSIST_RADIUS = 1.5;
   private static final double VIEW_DISTANCE_SQ = 16384.0;

   private LightningBeam() {
   }

   public static void fire(World world, PlayerEntity player, float power) {
      if (world instanceof ServerWorld serverWorld) {
         Vec3d direction = player.getRotationVec(1.0F).normalize();
         Vec3d start = origin(player, direction);
         double range = 8.0 + 16.0 * MathHelper.clamp(power, 0.0F, 1.0F);
         Vec3d reach = start.add(direction.multiply(range));
         BlockHitResult blockHit = world.raycast(new RaycastContext(start, reach, ShapeType.COLLIDER, FluidHandling.NONE, player));
         Vec3d end = blockHit.getType() == Type.MISS ? reach : blockHit.getPos();
         Box searchBox = player.getBoundingBox().stretch(direction.multiply(range)).expand(1.0);
         EntityHitResult entityHit = ProjectileUtil.raycast(
            player, start, end, searchBox, candidate -> candidate != player && candidate.canHit() && !candidate.isSpectator(), range * range
         );
         Entity target = null;
         if (entityHit != null) {
            target = entityHit.getEntity();
            end = entityHit.getPos();
         } else {
            Entity assisted = findAssistedTarget(serverWorld, player, start, direction, range, end);
            if (assisted != null) {
               target = assisted;
               end = assisted.getBoundingBox().getCenter();
            }
         }

         if (target != null) {
            target.setOnFireFor(5.0F);
            target.damage(world.getDamageSources().indirectMagic(player, player), 10.0F);
         }

         LightningBeamPayload payload = new LightningBeamPayload(start, end, world.random.nextInt());

         for (ServerPlayerEntity viewer : serverWorld.getPlayers()) {
            if (viewer.squaredDistanceTo(start) < 16384.0) {
               ServerPlayNetworking.send(viewer, payload);
            }
         }

         serverWorld.playSound(null, end.x, end.y, end.z, SoundEvents.ENTITY_LIGHTNING_BOLT_IMPACT, SoundCategory.PLAYERS, 0.8F, 1.5F);
         serverWorld.spawnParticles(ParticleTypes.ELECTRIC_SPARK, end.x, end.y, end.z, 16, 0.35, 0.35, 0.35, 0.3);
         Vec3d delta = end.subtract(start);
         double length = delta.length();
         if (length > 0.5) {
            Vec3d unit = delta.multiply(1.0 / length);
            double from = Math.min(1.5, length * 0.5);
            int sparks = MathHelper.clamp((int)((length - from) / 0.8), 4, 40);

            for (int i = 0; i <= sparks; i++) {
               Vec3d point = start.add(unit.multiply(from + (length - from) * i / sparks));
               serverWorld.spawnParticles(ParticleTypes.ELECTRIC_SPARK, point.x, point.y, point.z, 1, 0.04, 0.04, 0.04, 0.0);
            }
         }
      }
   }

   public static Vec3d origin(PlayerEntity player, Vec3d look) {
      Vec3d right = perpendicularHorizontal(look);
      return player.getEyePos().add(look.multiply(0.9)).add(right.multiply(0.3)).add(0.0, -0.25, 0.0);
   }

   private static Entity findAssistedTarget(ServerWorld world, PlayerEntity player, Vec3d start, Vec3d direction, double range, Vec3d limit) {
      double maxDistance = limit.distanceTo(start);
      Box box = player.getBoundingBox().stretch(direction.multiply(range)).expand(2.0);
      List<Entity> candidates = world.getOtherEntities(
         player, box, candidatex -> candidatex.canHit() && !candidatex.isSpectator() && candidatex.isAlive()
      );
      Entity best = null;
      double bestLateral = 1.5;

      for (Entity candidate : candidates) {
         Vec3d center = candidate.getBoundingBox().getCenter();
         Vec3d toTarget = center.subtract(start);
         double along = toTarget.dotProduct(direction);
         if (!(along <= 0.5) && !(along > maxDistance)) {
            double lateral = toTarget.subtract(direction.multiply(along)).length();
            if (!(lateral >= bestLateral)) {
               BlockHitResult wall = world.raycast(new RaycastContext(start, center, ShapeType.COLLIDER, FluidHandling.NONE, player));
               if (wall.getType() == Type.MISS) {
                  bestLateral = lateral;
                  best = candidate;
               }
            }
         }
      }

      return best;
   }

   public static Vec3d perpendicularHorizontal(Vec3d look) {
      Vec3d right = new Vec3d(-look.z, 0.0, look.x);
      return right.lengthSquared() < 1.0E-4 ? new Vec3d(1.0, 0.0, 0.0) : right.normalize();
   }
}

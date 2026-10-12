package com.dsh.lightningsword.client;

import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext;
import net.minecraft.client.gl.RenderPipelines;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.RenderSetup;
import net.minecraft.util.math.Vec3d;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.util.math.random.Random;
import org.joml.Matrix4f;

public final class BeamRenderer {
   private static final float RED = 0.45F;
   private static final float GREEN = 0.45F;
   private static final float BLUE = 0.5F;
   private static final float ALPHA = 0.3F;
   private static final double VANILLA_LENGTH = 128.0;
   private static final float MIN_LENGTH = 0.5F;
   private static final double NEAR_CLIP = 2.2;

   /** Built once from the vanilla lightning pipeline, then reused for every bolt. */
   private static RenderLayer lightningLayer;

   private BeamRenderer() {
   }

   private static RenderLayer lightningLayer() {
      RenderLayer layer = lightningLayer;
      if (layer == null) {
         layer = RenderLayer.of("lightning_sword_bolt", RenderSetup.builder(RenderPipelines.RENDERTYPE_LIGHTNING).build());
         lightningLayer = layer;
      }
      return layer;
   }

   public static void render(WorldRenderContext context) {
      if (!ClientBeams.active().isEmpty()) {
         VertexConsumerProvider consumers = context.consumers();
         MatrixStack matrices = context.matrices();
         if (consumers != null && matrices != null) {
            Vec3d camera = context.gameRenderer().getCamera().getCameraPos();
            VertexConsumer buffer = consumers.getBuffer(lightningLayer());

            for (ClientBeams.Beam beam : ClientBeams.active()) {
               Vec3d delta = beam.end.subtract(beam.start);
               double length = delta.length();
               if (!(length < 0.5)) {
                  Vec3d axis = delta.multiply(1.0 / length);
                  Vec3d from = beam.start;
                  double skip = 2.2 - from.distanceTo(camera);
                  if (skip > 0.0) {
                     if (length - skip < 0.5) {
                        continue;
                     }

                     from = from.add(axis.multiply(skip));
                     length -= skip;
                  }

                  Vec3d side = axis.crossProduct(Math.abs(axis.y) > 0.99 ? new Vec3d(1.0, 0.0, 0.0) : new Vec3d(0.0, 1.0, 0.0))
                     .normalize();
                  Vec3d up = side.crossProduct(axis).normalize();
                  double scale = length / 128.0;
                  Vec3d relative = from.subtract(camera);
                  matrices.push();
                  matrices.translate(relative.x, relative.y, relative.z);
                  Matrix4f matrix = matrices.peek().getPositionMatrix();
                  buildBolt(matrix, buffer, axis, side, up, scale, beam.shapeSeed(), beam.fade());
                  matrices.pop();
               }
            }
         }
      }
   }

   private static void buildBolt(Matrix4f matrix, VertexConsumer buffer, Vec3d axis, Vec3d side, Vec3d up, double scale, int seed, float fade) {
      float[] xs = new float[8];
      float[] zs = new float[8];
      float driftX = 0.0F;
      float driftZ = 0.0F;
      Random random = Random.create(seed);

      for (int step = 7; step >= 0; step--) {
         xs[step] = driftX;
         zs[step] = driftZ;
         driftX += random.nextInt(11) - 5;
         driftZ += random.nextInt(11) - 5;
      }

      for (int layer = 0; layer < 4; layer++) {
         Random branchRandom = Random.create(seed);

         for (int branch = 0; branch < 3; branch++) {
            int top = branch > 0 ? 7 - branch : 7;
            int bottom = branch > 0 ? top - 2 : 0;
            float x = xs[top] - driftX;
            float z = zs[top] - driftZ;

            for (int step = top; step >= bottom; step--) {
               float previousX = x;
               float previousZ = z;
               if (branch == 0) {
                  x += branchRandom.nextInt(11) - 5;
                  z += branchRandom.nextInt(11) - 5;
               } else {
                  x += branchRandom.nextInt(31) - 15;
                  z += branchRandom.nextInt(31) - 15;
               }

               float widthNear = 0.1F + layer * 0.2F;
               if (branch == 0) {
                  widthNear *= step * 0.1F + 1.0F;
               }

               float widthFar = 0.1F + layer * 0.2F;
               if (branch == 0) {
                  widthFar *= (step - 1.0F) * 0.1F + 1.0F;
               }

               drawBranch(matrix, buffer, axis, side, up, scale, fade, x, z, step, previousX, previousZ, widthNear, widthFar, false, false, true, false);
               drawBranch(matrix, buffer, axis, side, up, scale, fade, x, z, step, previousX, previousZ, widthNear, widthFar, true, false, true, true);
               drawBranch(matrix, buffer, axis, side, up, scale, fade, x, z, step, previousX, previousZ, widthNear, widthFar, true, true, false, true);
               drawBranch(matrix, buffer, axis, side, up, scale, fade, x, z, step, previousX, previousZ, widthNear, widthFar, false, true, false, false);
            }
         }
      }
   }

   private static void drawBranch(
      Matrix4f matrix,
      VertexConsumer buffer,
      Vec3d axis,
      Vec3d side,
      Vec3d up,
      double scale,
      float fade,
      float x1,
      float z1,
      int y,
      float x2,
      float z2,
      float offset1,
      float offset2,
      boolean shiftEast1,
      boolean shiftSouth1,
      boolean shiftEast2,
      boolean shiftSouth2
   ) {
      vertex(matrix, buffer, axis, side, up, scale, fade, x1 + (shiftEast1 ? offset1 : -offset1), y * 16.0F, z1 + (shiftSouth1 ? offset1 : -offset1));
      vertex(matrix, buffer, axis, side, up, scale, fade, x2 + (shiftEast1 ? offset2 : -offset2), (y + 1) * 16.0F, z2 + (shiftSouth1 ? offset2 : -offset2));
      vertex(matrix, buffer, axis, side, up, scale, fade, x2 + (shiftEast2 ? offset2 : -offset2), (y + 1) * 16.0F, z2 + (shiftSouth2 ? offset2 : -offset2));
      vertex(matrix, buffer, axis, side, up, scale, fade, x1 + (shiftEast2 ? offset1 : -offset1), y * 16.0F, z1 + (shiftSouth2 ? offset1 : -offset1));
   }

   private static void vertex(
      Matrix4f matrix, VertexConsumer buffer, Vec3d axis, Vec3d side, Vec3d up, double scale, float fade, float localX, float localY, float localZ
   ) {
      Vec3d position = axis.multiply(localY * scale).add(side.multiply(localX * scale)).add(up.multiply(localZ * scale));
      buffer.vertex(matrix, (float)position.x, (float)position.y, (float)position.z)
         .color(0.45F, 0.45F, 0.5F, 0.3F * fade);
   }
}

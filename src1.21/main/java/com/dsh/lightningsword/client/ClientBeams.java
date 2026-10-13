package com.dsh.lightningsword.client;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.minecraft.util.math.Vec3d;

public final class ClientBeams {
   public static final int LIFE = 5;
   private static final List<ClientBeams.Beam> BEAMS = new ArrayList<>();

   private ClientBeams() {
   }

   public static void add(Vec3d start, Vec3d end, int seed) {
      BEAMS.add(new ClientBeams.Beam(start, end, seed));
   }

   public static List<ClientBeams.Beam> active() {
      return BEAMS;
   }

   public static void tick() {
      Iterator<ClientBeams.Beam> iterator = BEAMS.iterator();

      while (iterator.hasNext()) {
         ClientBeams.Beam beam = iterator.next();
         if (--beam.life <= 0) {
            iterator.remove();
         }
      }
   }

   public static final class Beam {
      public final Vec3d start;
      public final Vec3d end;
      public final int seed;
      public int life = 5;

      Beam(Vec3d start, Vec3d end, int seed) {
         this.start = start;
         this.end = end;
         this.seed = seed;
      }

      public float fade() {
         return Math.min(1.0F, this.life / 2.0F);
      }

      public int shapeSeed() {
         return this.seed + (5 - this.life);
      }
   }
}

package com.dsh.lightningsword.network;

import com.dsh.lightningsword.LightningSwordMod;
import net.minecraft.util.math.Vec3d;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.packet.CustomPayload.Id;

public record LightningBeamPayload(Vec3d start, Vec3d end, int seed) implements CustomPayload {
   public static final Id<LightningBeamPayload> ID = new Id<>(LightningSwordMod.id("beam"));
   public static final PacketCodec<RegistryByteBuf, LightningBeamPayload> CODEC = PacketCodec.of((value, buf) -> {
      writeVec(buf, value.start);
      writeVec(buf, value.end);
      buf.writeInt(value.seed);
   }, buf -> new LightningBeamPayload(readVec(buf), readVec(buf), buf.readInt()));

   private static void writeVec(RegistryByteBuf buf, Vec3d vec) {
      buf.writeDouble(vec.x);
      buf.writeDouble(vec.y);
      buf.writeDouble(vec.z);
   }

   private static Vec3d readVec(RegistryByteBuf buf) {
      return new Vec3d(buf.readDouble(), buf.readDouble(), buf.readDouble());
   }

   public Id<? extends CustomPayload> getId() {
      return ID;
   }
}

package com.dsh.lightningsword.client;

import com.dsh.lightningsword.LightningSwordMod;
import com.dsh.lightningsword.ModItems;
import com.dsh.lightningsword.network.LightningBeamPayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.item.ModelPredicateProviderRegistry;

public class LightningSwordClient implements ClientModInitializer {

   public void onInitializeClient() {
         SwordSprites.init();
      
      ClientPlayNetworking.registerGlobalReceiver(
              LightningBeamPayload.ID,
              (payload, context) ->
                      context.client().execute(() ->
                              ClientBeams.add(payload.start(), payload.end(), payload.seed())
                      )
      );

      WorldRenderEvents.AFTER_TRANSLUCENT.register(BeamRenderer::render);

      ClientTickEvents.END_CLIENT_TICK.register(client -> {
         ClientBeams.tick();
         SwordSprites.markSpritesActive();
      });

      ModelPredicateProviderRegistry.register(
              ModItems.LIGHTNING_SWORD,
              LightningSwordMod.id("aim"),
              (stack, world, entity, seed) ->
                      entity != null && entity.isUsingItem() ? 0.75F : 0.0F
      );
   }
}

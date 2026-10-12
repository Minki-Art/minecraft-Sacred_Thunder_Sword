package com.dsh.lightningsword.client;

import com.dsh.lightningsword.network.LightningBeamPayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderEvents;

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

      // The bolt is submitted the same way vanilla submits its own lightning entity:
      // a custom command on the world render queue with the vanilla lightning layer, which
      // composites in the weather stage (after terrain and translucency).
      // The charging pose is data-driven in 1.21.11: assets/lightning_sword/items/lightning_sword.json
      // switches on the vanilla minecraft:using_item property, so no predicate registration is needed.
      WorldRenderEvents.BEFORE_ENTITIES.register(BeamRenderer::render);

      ClientTickEvents.END_CLIENT_TICK.register(client -> {
         ClientBeams.tick();
         SwordSprites.markSpritesActive();
      });
   }
}

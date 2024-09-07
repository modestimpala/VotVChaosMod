local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local World = UEHelpers:GetWorld()

        local spawn = World:SpawnActor(StaticFindObject("/Game/Mods/ChaosMod/Assets/shopOrderHandler.shopOrderHandler_C"), {}, {}, false, nil, nil, false, false)

        spawn:placeOrder(FName("shrimp"), 1)

        ExecuteWithDelay(1000, function()
            spawn:K2_DestroyActor()
        end)

        return true
    end
}
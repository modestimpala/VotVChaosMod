local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local funguy = StaticFindObject("/Game/objects/npc/funguy.funguy_C")
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local SpawnedActor = World:SpawnActor(funguy, Location, Rotation, false, nil, nil, false, false)
        if SpawnedActor:IsValid() then
            print("[MyLuaMod] Spawned funguy")
            local PreBeginPlay = SpawnedActor.ReceiveBeginPlay
            if PreBeginPlay:IsValid() then
                PreBeginPlay(SpawnedActor)
            end
            return true
        else 
            print("[MyLuaMod] Failed to spawn funguy")
            return false
        end
    end
}
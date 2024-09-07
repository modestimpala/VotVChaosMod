local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local pyramid = StaticFindObject("/Game/objects/piramid2.piramid2_C")
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()
        local Location = {X=1121.955, Y=648.347, Z=6185.325}
        local Rotation = {Pitch=0, Yaw=0, Roll=0}
        local SpawnedActor = World:SpawnActor(pyramid, Location, Rotation, false, nil, nil, false, false)
        if SpawnedActor:IsValid() then
            print("[MyLuaMod] Spawned pyramid")
            local PreBeginPlay = SpawnedActor.ReceiveBeginPlay
            if PreBeginPlay:IsValid() then
                PreBeginPlay(SpawnedActor)
            end
            return true
        else 
            print("[MyLuaMod] Failed to spawn pyramid")
            return false
        end
    end
}
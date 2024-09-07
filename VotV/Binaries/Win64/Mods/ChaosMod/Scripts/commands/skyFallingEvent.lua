local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers.GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local obj_C = StaticFindObject("/Game/objects/misc/skyFallingEvent.skyFallingEvent_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local obj = World:SpawnActor(obj_C, Location, Rotation, false, nil, nil, false, false)
        obj:ReceiveBeginPlay()
        ExecuteWithDelay(60000, function()
            if obj:IsValid() then
                obj:K2_DestroyActor()
            end
        end)
        return true
    end
}
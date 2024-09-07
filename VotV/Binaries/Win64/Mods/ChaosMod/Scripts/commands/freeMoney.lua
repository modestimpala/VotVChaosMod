local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers.GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local obj_C = StaticFindObject("/Game/objects/misc/baocoin.baocoin_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local i = 0
        for i = 0, 30, 1 do
            local obj = World:SpawnActor(obj_C, Location, Rotation, false, nil, nil, false, false)
            obj:ReceiveBeginPlay()
        end
        return true
    end
}
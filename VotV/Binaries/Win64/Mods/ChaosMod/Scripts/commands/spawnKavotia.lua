local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local obj_C = StaticFindObject("/Game/objects/kavotia.kavotia_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = {Pitch=0, Yaw=0, Roll=0}
        Location = {X=Location.X, Y=Location.Y, Z=Location.Z + 20}

        local World = Pawn:GetWorld()
        local obj = World:SpawnActor(obj_C, Location, Rotation, false, nil, nil, false, false)
        obj:ReceiveBeginPlay()
        ExecuteWithDelay(90000, function()
            obj:K2_DestroyActor()
        end)
        return true
    end
}
local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local meatball_C = StaticFindObject("/Game/objects/prop_garbageClump.prop_garbageClump_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local meatball = World:SpawnActor(meatball_C, Location, Rotation, false, nil, nil, false, false)
        meatball.Type = 5
        meatball:ReceiveBeginPlay()
        return true
    end
}
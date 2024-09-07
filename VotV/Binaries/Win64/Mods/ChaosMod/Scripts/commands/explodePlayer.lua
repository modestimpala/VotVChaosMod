local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local explosion = StaticFindObject("/Game/objects/explosion.explosion_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local exp = World:SpawnActor(explosion, Location, Rotation, false, nil, nil, false, false)
        exp:ReceiveBeginPlay()
        return true
    end
}
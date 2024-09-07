local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local blackFog_C = StaticFindObject("/Game/objects/blackFog.blackFog_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local blackFog = World:SpawnActor(blackFog_C, Location, Rotation, false, nil, nil, false, false)
        blackFog:ReceiveBeginPlay()
        return true
    end
}
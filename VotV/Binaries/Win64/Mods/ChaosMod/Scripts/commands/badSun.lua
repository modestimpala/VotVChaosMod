local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local badSun_C = StaticFindObject("/Game/objects/badSun.badSun_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local badSun = World:SpawnActor(badSun_C, Location, Rotation, false, nil, nil, false, false)
        badSun:ReceiveBeginPlay()
        return true
    end
}
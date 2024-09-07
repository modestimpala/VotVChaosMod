local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local cig = StaticFindObject("/Game/objects/cig.cig_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local cig = World:SpawnActor(cig, Location, Rotation, false, nil, nil, false, false)
        Pawn.cig = cig
        cig.lit(true)
        return true
    end
}
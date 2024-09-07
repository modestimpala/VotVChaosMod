local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local jellyfish_C = StaticFindObject("/Game/objects/jellyfish.jellyfish_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local i = 0
        for i = 0, 20, 1 do
            local jellyfish = World:SpawnActor(jellyfish_C, Location, Rotation, false, nil, nil, false, false)
            jellyfish:ReceiveBeginPlay()
        end
        
        return true
    end
}
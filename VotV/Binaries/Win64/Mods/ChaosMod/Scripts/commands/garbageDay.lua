local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local garbage_C = StaticFindObject("/Game/objects/prop_garbageClump.prop_garbageClump_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local i = 0
        for i = 0, 40 do
            ExecuteWithDelay(25, function()
                Location = {X=Location.X + math.random(-100, 100), Y=Location.Y + math.random(-100, 100), Z=Location.Z + math.random(-100, 100)}
                local garbage = World:SpawnActor(garbage_C, Location, Rotation, false, nil, nil, false, false)
                garbage.Type = math.random(1, 4)
                garbage:ReceiveBeginPlay()
            end)
        end
        return true
    end
}
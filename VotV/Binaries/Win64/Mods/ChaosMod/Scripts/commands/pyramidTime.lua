local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local pyramid = StaticFindObject("/Game/objects/piramid2.piramid2_C")
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()
        local Location = {X=1121.955, Y=648.347, Z=6185.325}
        local Rotation = {Pitch=0, Yaw=0, Roll=0}
        local SpawnedActor = World:SpawnActor(pyramid, Location, Rotation, false, nil, nil, false, false)
        local randomTime = math.random(120000, 300000)
        ExecuteWithDelay(randomTime, function()
            if SpawnedActor:IsValid() then
                SpawnedActor:Destroy()
            end
        end)
        return true
    end
}
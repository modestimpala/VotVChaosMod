local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local radioTowerLoc =  {X=1954.681, Y=-2736.888, Z=15426.764}

        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()
        local Location = radioTowerLoc
        local Rotation = {Pitch = 0, Yaw = 0, Roll = 0}
        local fOut = {}
        local mainGamemode_C = FindFirstOf("mainGamemode_C")
        mainGamemode_C.backroomsEnabled = false
        Pawn:unsit()
        Pawn:K2_SetActorLocation(Location, false, fOut, false)
        ExecuteWithDelay(1000, function()
            mainGamemode_C.backroomsEnabled = true
        end)
    end
}
local UEHelpers = require("UEHelpers")
  
return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()

        mainGame:photo(Location, Rotation, true)
        return true
    end
}
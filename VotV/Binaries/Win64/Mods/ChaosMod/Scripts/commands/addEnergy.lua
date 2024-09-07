local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers.GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local cake = StaticFindObject("/Game/objects/prop_food_cake.prop_food_cake_C")
        local out = {}
        local out2 = nil
        Pawn:addFood(0, 45, 0, cake, false, out)
        return true
    end
}
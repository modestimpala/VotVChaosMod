local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local cars = FindAllOf("car1_C")
        for _, car in pairs(cars) do
            car.health = 0
            car.broken = true
            car:broken()
            local vector = car:K2_GetActorLocation()
            car:explode(vector)
        end
        return true
    end
}
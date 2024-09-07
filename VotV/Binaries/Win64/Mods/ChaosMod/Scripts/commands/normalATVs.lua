local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local cars = FindAllOf("car1_C")
        for _, car in pairs(cars) do
            car.Speed = 2000
            car.speed_default = 2000
            car.speed_turbo = 4000
            car.torqAlpha = 0
        end
        return true
    end
}
local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local cars = FindAllOf("car1_C")
        for _, car in pairs(cars) do
            car.health = 100
            car.brokenn = false
        end
        return true
    end
}
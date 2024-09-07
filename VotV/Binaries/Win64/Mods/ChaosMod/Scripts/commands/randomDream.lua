local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local dreams = {
            StaticFindObject("/Game/objects/dreams/dream_run.dream_run_C"),
            StaticFindObject("/Game/objects/dreams/dream_room.dream_room_C"),
            StaticFindObject("/Game/objects/dreams/dream_wend.dream_wend_C"),
            StaticFindObject("/Game/objects/dreams/dream_mann.dream_mann_C"),
            StaticFindObject("/Game/objects/dreams/dream_jump.dream_jump_C"),
            StaticFindObject("/Game/objects/dreams/dream_fill.dream_fill_C"),
            StaticFindObject("/Game/objects/dreams/dream_climb.dream_climb_C"),
            StaticFindObject("/Game/objects/dreams/dream_burger.dream_burger_C"),
            StaticFindObject("/Game/objects/dreams/dream_ufo.dream_ufo_C"),
            StaticFindObject("/Game/objects/dreams/dream_boulders.dream_boulders_C")
        }
        local dream = dreams[math.random(#dreams)]
        local mainGame = FindFirstOf("mainGamemode_C")
        mainGame:createDream(dream)
    end
}
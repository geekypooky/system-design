local stock_key = KEYS[1]
local reserved_key = KEYS[2]
local req_quantity = tonumber(ARGV[1])

local stock = tonumber(redis.call('get', stock_key)) or 0
if stock >= req_quantity then
    redis.call('decrby', stock_key, req_quantity)
    redis.call('incrby', reserved_key, req_quantity)
    return 1
else
    return 0
end

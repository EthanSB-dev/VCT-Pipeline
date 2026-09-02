-- Intermediate model: unnests the opponents + results arrays so each
-- match produces exactly two rows (one per participating team), each
-- carrying that team's score and whether they won. This is the join
-- key between matches and teams for downstream marts.

with staged as (

    select * from {{ ref('stg_matches') }}

),

opponents as (

    select
        match_id,
        (opponent->'opponent'->>'id')::bigint       as team_id,
        (opponent->'opponent'->>'name')::text       as team_name,
        (opponent->'opponent'->>'acronym')::text    as team_acronym,
        (opponent->'opponent'->>'location')::text   as team_location
    from staged,
         jsonb_array_elements(opponents_json) as opponent

),

results as (

    select
        match_id,
        (result->>'team_id')::bigint  as team_id,
        (result->>'score')::int       as score
    from staged,
         jsonb_array_elements(results_json) as result

),

joined as (

    select
        o.match_id,
        o.team_id,
        o.team_name,
        o.team_acronym,
        o.team_location,
        r.score,
        s.winner_id,
        (o.team_id = s.winner_id) as is_winner
    from opponents o
    left join results r
        on o.match_id = r.match_id
       and o.team_id = r.team_id
    left join staged s
        on o.match_id = s.match_id

)

select * from joined
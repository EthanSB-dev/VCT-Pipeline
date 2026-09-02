-- Marts model: one row per team, with aggregate performance stats
-- across all flagship VCT matches in the warehouse.

with match_teams as (

    select * from {{ ref('int_match_teams') }}

),

aggregated as (

    select
        team_id,
        max(team_name)      as team_name,
        max(team_acronym)   as team_acronym,
        max(team_location)  as team_location,
        count(distinct match_id)                          as matches_played,
        count(distinct match_id) filter (where is_winner)  as matches_won,
        round(
            100.0 * count(distinct match_id) filter (where is_winner)
            / nullif(count(distinct match_id), 0),
            1
        ) as win_rate_pct

    from match_teams
    group by team_id

)

select * from aggregated
order by matches_played desc
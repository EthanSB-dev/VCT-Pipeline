-- Marts model: one row per tournament/serie, with league context and
-- match counts, for grouping matches into their competitive context.

with staged as (

    select * from {{ ref('stg_matches') }}

),

aggregated as (

    select
        tournament_id,
        max(tournament_name)    as tournament_name,
        max(tournament_tier)    as tournament_tier,
        max(tournament_region)  as tournament_region,
        serie_id,
        max(serie_full_name)    as serie_full_name,
        max(serie_year)         as serie_year,
        league_id,
        max(league_name)        as league_name,
        count(distinct match_id) as matches_played,
        min(begin_at)            as earliest_match_at,
        max(end_at)              as latest_match_at

    from staged
    group by tournament_id, serie_id, league_id

)

select * from aggregated
order by latest_match_at desc
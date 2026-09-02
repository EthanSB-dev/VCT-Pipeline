-- Staging model: flattens the top-level fields of each raw VCT match
-- payload into typed columns. One row per match. Minimal logic — just
-- casting and renaming, per dbt staging-layer conventions.

with source as (

    select
        match_id,
        raw_payload
    from {{ source('raw', 'raw_matches') }}

),

flattened as (

    select
        match_id,

        (raw_payload->>'name')::text                          as match_name,
        (raw_payload->>'status')::text                         as match_status,
        (raw_payload->>'match_type')::text                     as match_type,
        (raw_payload->>'number_of_games')::int                 as number_of_games,
        (raw_payload->>'forfeit')::boolean                     as is_forfeit,

        (raw_payload->>'begin_at')::timestamptz                as begin_at,
        (raw_payload->>'end_at')::timestamptz                  as end_at,
        (raw_payload->>'scheduled_at')::timestamptz            as scheduled_at,
        (raw_payload->>'modified_at')::timestamptz             as modified_at,

        (raw_payload->>'winner_id')::bigint                    as winner_id,
        (raw_payload->'winner'->>'name')::text                 as winner_name,
        (raw_payload->>'winner_type')::text                    as winner_type,

        (raw_payload->'serie'->>'id')::bigint                  as serie_id,
        (raw_payload->'serie'->>'full_name')::text             as serie_full_name,
        (raw_payload->'serie'->>'year')::int                   as serie_year,

        (raw_payload->'league'->>'id')::bigint                 as league_id,
        (raw_payload->'league'->>'name')::text                 as league_name,

        (raw_payload->'tournament'->>'id')::bigint             as tournament_id,
        (raw_payload->'tournament'->>'name')::text             as tournament_name,
        (raw_payload->'tournament'->>'tier')::text             as tournament_tier,
        (raw_payload->'tournament'->>'region')::text           as tournament_region,

        (raw_payload->'videogame_version'->>'name')::text      as videogame_version,

        raw_payload->'opponents'                               as opponents_json,
        raw_payload->'results'                                 as results_json

    from source

)

select * from flattened
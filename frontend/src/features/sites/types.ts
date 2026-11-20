/**
 * Gym site record exposed to the frontend.
 *
 * @remarks
 * The API adapter maps the database-oriented `id_site` and
 * `registration_date` fields to the frontend's camelCase domain model.
 */
export interface Site {
  /** Unique identifier assigned by the backend or mock repository. */
  id: string;
  /** Required unique site name. */
  name: string;
  /** Required physical address of the gym site. */
  address: string;
  /** Date on which the site was registered. */
  registrationDate?: string;
  /** Last update timestamp when supplied by the backend. */
  updatedAt?: string;
}

/**
 * Fields accepted by site create and update operations.
 */
export interface SiteInput {
  /** Required unique site name. */
  name: string;
  /** Required physical address. */
  address: string;
}

/** Contract shared by the real and in-memory site API implementations. */
export interface SiteApi {
  /** Retrieves all gym sites. */
  list(): Promise<Site[]>;
  /** Creates a gym site. */
  create(input: SiteInput): Promise<Site>;
  /** Updates a gym site. */
  update(id: string, input: SiteInput): Promise<Site>;
  /** Deletes a gym site. */
  remove(id: string): Promise<undefined>;
}
